# unity_controller/dialogue_loop.py
# Main dialogue loop for Unity mode — with pre-computation for seamless transitions

import asyncio
import random
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


async def run_dialogue_loop(controller: 'UnityDialogueController'):
    """
    Main dialogue loop with pre-computation.

    While the current speaker's audio plays, the next turn's LLM inference
    and TTS generation run in parallel, eliminating perceived thinking delay.
    """
    topic = controller.dialogue_topic
    prefetched = None  # Stores pre-computed turn result

    while not controller.should_stop:
        # ── Pause check ──
        if controller.is_paused:
            print("[Dialogue] Paused - sending notification to Unity")
            await controller.ws_server.send_event("paused", {})
            while controller.is_paused and not controller.should_stop:
                await asyncio.sleep(0.1)
            if controller.should_stop:
                break
            print("[Dialogue] Resumed - continuing loop")
            prefetched = None  # Discard any stale prefetch after resume
            continue

        if controller.is_answering_question:
            await asyncio.sleep(0.1)
            continue

        # ── Get turn data (prefetched or generate now) ──
        if prefetched:
            turn_data = prefetched
            prefetched = None
            print(f"[Dialogue] Using pre-computed response for {turn_data['speaker'].name}")
        else:
            turn_data = await _generate_turn(controller, topic)

        speaker = turn_data['speaker']
        reply = turn_data['reply']
        audio_path = turn_data['audio_path']
        viseme_data = turn_data['viseme_data']
        stance = turn_data['stance']
        other_names = turn_data['other_names']

        # ── Send to Unity ──
        # Brief "thinking" notification for camera transition
        await controller.ws_server.send_agent_speaking(speaker.name, controller.last_speaker)
        # Short delay for camera to start moving
        await asyncio.sleep(0.5)

        # Detect invitation for next speaker
        controller.next_speaker_override = _detect_invited_speaker(reply, other_names)

        # Send response
        await controller.ws_server.send_agent_response(
            agent_name=speaker.name,
            text=reply,
            audio_path=audio_path,
            viseme_data=viseme_data,
            stance=stance,
            turn=controller.speech_count
        )

        # ── Update state ──
        controller.last_speaker = speaker.name
        speaker.add_memory(turn_data['user_prompt'], reply)
        controller.history.append({"agent": speaker.name, "response": reply})
        controller.speech_count += 1

        # Log utterance
        motivation_snapshot = {a.name: a.motivation_score for a in controller.agents}
        controller.logger.log_utterance(
            speaker=speaker.name,
            content=reply,
            turn=controller.speech_count,
            is_qa=False,
            stance=stance,
            motivation_scores=motivation_snapshot
        )

        # Update motivation scores
        controller.motivation_scorer.analyze_utterance(
            speaker_name=speaker.name,
            text=reply,
            all_agents=controller.agents,
            recent_history=controller.history[-5:],
            conviviality=controller.conviviality
        )

        motivation_scores = {a.name: a.motivation_score for a in controller.agents}
        await controller.ws_server.send_motivation_update(motivation_scores)

        print(f"[{speaker.name}] {reply}\n")

        # ── Start pre-computation for next turn while audio plays ──
        controller.prefetch_task = asyncio.create_task(
            _generate_turn(controller, topic)
        )

        # ── Wait for audio playback ──
        words = len(reply.split())
        estimated_duration = max(2.0, words / 2.5)
        thinking_pause = 0.5
        total_wait = estimated_duration + thinking_pause
        print(f"[Dialogue] Waiting {total_wait:.1f}s for audio, pre-computing next turn...")

        sleep_remaining = total_wait
        while sleep_remaining > 0:
            await asyncio.sleep(min(0.5, sleep_remaining))
            sleep_remaining -= 0.5

        # ── Collect prefetch result ──
        if controller.prefetch_task and not controller.prefetch_task.cancelled():
            try:
                if controller.prefetch_task.done():
                    prefetched = controller.prefetch_task.result()
                    print(f"[Dialogue] Pre-computation ready: {prefetched['speaker'].name}")
                else:
                    # Audio finished but LLM/TTS still running — wait for it
                    print("[Dialogue] Waiting for pre-computation to finish...")
                    prefetched = await controller.prefetch_task
                    print(f"[Dialogue] Pre-computation complete: {prefetched['speaker'].name}")
            except asyncio.CancelledError:
                prefetched = None
            except Exception as e:
                print(f"[Dialogue] Pre-computation error: {e}")
                prefetched = None
        else:
            prefetched = None

        controller.prefetch_task = None

    print("[Dialogue] Main loop ended normally")


async def _generate_turn(controller: 'UnityDialogueController', topic: str) -> dict:
    """
    Generate a complete turn: select speaker, build prompt, call LLM, generate TTS.

    Returns a dict with all data needed to send the response.
    """
    # ── Select speaker ──
    if controller.resume_same_speaker and controller.last_speaker:
        speaker = next(
            (a for a in controller.agents if a.name == controller.last_speaker),
            None
        )
        if speaker is None:
            speaker = controller.speaker_selector.select_next_speaker()
        controller.resume_same_speaker = False
    elif getattr(controller, 'next_speaker_override', None):
        override_name = controller.next_speaker_override
        controller.next_speaker_override = None
        speaker = next(
            (a for a in controller.agents if a.name == override_name),
            controller.speaker_selector.select_next_speaker()
        )
    else:
        speaker = controller.speaker_selector.select_next_speaker()

    # ── Analyze stance ──
    stance = controller.stance_analyzer.analyze_stance(
        agent=speaker,
        recent_history=controller.history[-3:],
        conviviality=controller.conviviality
    )

    tone_instruction = controller.stance_analyzer.get_tone_instruction(
        stance=stance,
        conviviality=controller.conviviality
    )

    # ── Build prompt ──
    context = controller.build_context()
    context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

    other_names = [a.name for a in controller.agents if a.name != speaker.name]
    others_str = ", ".join(other_names)

    ref_instruction = (
        f"- Where it genuinely fits, reference one of your own works by name.\n"
        if random.random() < 0.6 else ""
    )
    invite_instruction = (
        f"- End with a direct question to one of the other philosophers ({others_str}) by name.\n"
        if random.random() < 0.3 else ""
    )

    engagement_instruction = ""
    if controller.last_speaker:
        engagement_instruction = (
            f"- Directly engage with a specific argument {controller.last_speaker} just made — "
            f"challenge it, qualify it, or build on it with your own reasoning. "
            f"Do NOT use generic openers like 'I see your point' or 'Indeed'; instead, name the argument and take a position on it.\n"
        )

    length_roll = random.random()
    if length_roll < 0.35:
        length_instruction = "Reply with a single short reaction — under 20 words, no complex clauses."
        target_sentences = 1
    elif length_roll < 0.75:
        length_instruction = "Reply in two sentences."
        target_sentences = 2
    else:
        length_instruction = "Reply in three sentences."
        target_sentences = 3

    max_tokens = 40 if target_sentences == 1 else 150

    user_prompt = (
        f"Debate topic: {topic}\n\n"
        f"{context_block}"
        f"Respond to this debate directly in first person.\n"
        f"- {length_instruction}\n"
        f"- {tone_instruction}\n"
        f"{engagement_instruction}"
        f"- Do NOT simply restate your own views from scratch — your response must be shaped by what was just said.\n"
        f"{ref_instruction}"
        f"{invite_instruction}"
        f"- Do NOT say 'As {speaker.name}' or refer to yourself in third person.\n"
    )

    # ── LLM generation ──
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(
        None,
        controller.model_manager.chat_once,
        speaker.model_key,
        speaker.system_prompt,
        user_prompt,
        max_tokens,
        0.7,
    )

    reply = reply.replace("\n", " ").strip()
    reply = _clean_reply(reply, speaker.name)

    # Trim to target sentence count
    sentences = re.split(r'(?<=[.!?])\s+', reply.strip())
    sentences = [s for s in sentences if s.strip()]
    if len(sentences) > target_sentences:
        reply = " ".join(sentences[:target_sentences])
        if reply[-1] not in '.!?':
            reply += '.'

    # ── TTS generation ──
    audio_path, viseme_data = await controller.generate_speech(speaker.name, reply)

    return {
        'speaker': speaker,
        'reply': reply,
        'audio_path': audio_path,
        'viseme_data': viseme_data,
        'stance': stance,
        'other_names': other_names,
        'user_prompt': user_prompt,
    }


def _clean_reply(reply: str, speaker_name: str) -> str:
    """Remove speaker name prefix from reply if present."""
    if reply.startswith(speaker_name + ":"):
        reply = reply[len(speaker_name) + 1:].strip()
    elif reply.startswith(speaker_name):
        reply = reply[len(speaker_name):].strip()
        if reply.startswith(":"):
            reply = reply[1:].strip()
    return reply


def _detect_invited_speaker(reply: str, other_names: list) -> str | None:
    """
    Detect if the reply ends with a question directed at a specific philosopher.
    Returns the invited philosopher's name, or None.
    """
    if '?' not in reply:
        return None
    sentences = [s.strip() for s in reply.replace('?', '?.').split('.') if s.strip()]
    last = sentences[-1] if sentences else ""
    for name in other_names:
        if name in last:
            return name
    return None
