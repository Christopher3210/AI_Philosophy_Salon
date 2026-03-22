# unity_controller/dialogue_loop.py
# Main dialogue loop for Unity mode — with two-phase pre-computation

import asyncio
import random
import re
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


async def run_dialogue_loop(controller: 'UnityDialogueController'):
    """
    Main dialogue loop with two-phase pre-computation.

    Phase 1 (during audio): LLM inference for next turn (fast, ~3s)
    Phase 2 (after audio): TTS generation while showing "thinking" animation (~5-8s)

    User sees: Speaker finishes → camera moves to next → brief thinking → starts talking
    """
    topic = controller.dialogue_topic
    llm_prefetch = None  # Stores pre-computed LLM result (no audio yet)

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
            llm_prefetch = None
            continue

        if controller.is_answering_question:
            await asyncio.sleep(0.1)
            continue

        # ── Phase 1: Get LLM result (prefetched or generate now) ──
        if llm_prefetch:
            llm_data = llm_prefetch
            llm_prefetch = None
            print(f"[Dialogue] Using pre-computed LLM for {llm_data['speaker'].name}")
        else:
            llm_data = await _generate_llm(controller, topic)

        speaker = llm_data['speaker']
        reply = llm_data['reply']
        stance = llm_data['stance']
        other_names = llm_data['other_names']

        # ── Show thinking animation while TTS generates ──
        await controller.ws_server.send_agent_speaking(speaker.name, controller.last_speaker)

        # Detect invitation for next speaker
        controller.next_speaker_override = _detect_invited_speaker(reply, other_names)

        # ── Phase 2: Generate TTS (user sees thinking animation) ──
        print(f"[Dialogue] Generating TTS for {speaker.name}...")
        audio_path, viseme_data = await controller.generate_speech(speaker.name, reply)

        # Send response — starts playing immediately
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
        speaker.add_memory(llm_data['user_prompt'], reply)
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

        # ── Start LLM-only prefetch for next turn while audio plays ──
        controller.prefetch_task = asyncio.create_task(
            _generate_llm(controller, topic)
        )

        # ── Wait for audio playback ──
        if viseme_data:
            last = viseme_data[-1]
            audio_duration = last["time"] + last["duration"]
        else:
            audio_duration = max(2.0, len(reply.split()) / 2.5)
        thinking_pause = 0.5
        total_wait = audio_duration + thinking_pause
        print(f"[Dialogue] Waiting {total_wait:.1f}s for audio, pre-computing next LLM...")

        sleep_remaining = total_wait
        while sleep_remaining > 0:
            await asyncio.sleep(min(0.5, sleep_remaining))
            sleep_remaining -= 0.5

        # ── Collect LLM prefetch result ──
        if controller.prefetch_task and not controller.prefetch_task.cancelled():
            try:
                if controller.prefetch_task.done():
                    llm_prefetch = controller.prefetch_task.result()
                    print(f"[Dialogue] LLM pre-computed: {llm_prefetch['speaker'].name}")
                else:
                    # Audio finished but LLM still running — wait for it (should be fast)
                    print("[Dialogue] Waiting for LLM pre-computation...")
                    llm_prefetch = await controller.prefetch_task
                    print(f"[Dialogue] LLM ready: {llm_prefetch['speaker'].name}")
            except asyncio.CancelledError:
                llm_prefetch = None
            except Exception as e:
                print(f"[Dialogue] Pre-computation error: {e}")
                llm_prefetch = None
        else:
            llm_prefetch = None

        controller.prefetch_task = None

        # ── Check if debate time is up ──
        if _is_time_up(controller):
            print("[Dialogue] Time is up — entering summary phase")
            llm_prefetch = None
            await _run_summary_phase(controller, topic)
            controller.should_stop = True
            break

    print("[Dialogue] Main loop ended normally")


async def _generate_llm(controller: 'UnityDialogueController', topic: str) -> dict:
    """
    Phase 1: Select speaker, build prompt, call LLM. No TTS.
    Fast enough (~3s) to complete during audio playback.
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

    max_tokens = 40 if target_sentences == 1 else 100

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

    return {
        'speaker': speaker,
        'reply': reply,
        'stance': stance,
        'other_names': other_names,
        'user_prompt': user_prompt,
    }


def _is_time_up(controller: 'UnityDialogueController') -> bool:
    """Check if the debate duration has been exceeded."""
    if controller.debate_duration <= 0:
        return False
    if controller.debate_start_time is None:
        return False
    elapsed = time.time() - controller.debate_start_time
    return elapsed >= controller.debate_duration


async def _run_summary_phase(controller: 'UnityDialogueController', topic: str):
    """
    Each philosopher gives a final summative statement referencing
    what they said during the debate.
    """
    print("\n" + "=" * 50)
    print("  SUMMARY PHASE")
    print("=" * 50)

    # Gather each agent's own statements from history
    agent_statements = {}
    for agent in controller.agents:
        own = [h["response"] for h in controller.history if h["agent"] == agent.name]
        agent_statements[agent.name] = own

    for agent in controller.agents:
        if controller.should_stop:
            break

        # Build summary of what this philosopher said
        own_statements = agent_statements.get(agent.name, [])
        if own_statements:
            # Include last few statements for context
            recent_own = own_statements[-3:]
            own_summary = "\n".join(f"- {s}" for s in recent_own)
            own_block = f"Your key arguments during this debate:\n{own_summary}\n\n"
        else:
            own_block = ""

        user_prompt = (
            f"Debate topic: {topic}\n\n"
            f"{own_block}"
            f"The debate is now concluding. Give your final summative statement in 2-3 sentences.\n"
            f"- Reflect on what you argued and what you learned from the other philosophers.\n"
            f"- Reference at least one specific point you made earlier.\n"
            f"- End with a concluding thought on the topic.\n"
            f"- Do NOT say 'As {agent.name}' or refer to yourself in third person.\n"
        )

        # Notify Unity
        await controller.ws_server.send_agent_speaking(agent.name, controller.last_speaker)

        # Generate LLM response
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(
            None,
            controller.model_manager.chat_once,
            agent.model_key,
            agent.system_prompt,
            user_prompt,
            150,
            0.7,
        )

        reply = reply.replace("\n", " ").strip()
        reply = _clean_reply(reply, agent.name)

        # Trim to 3 sentences max
        sentences = re.split(r'(?<=[.!?])\s+', reply.strip())
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > 3:
            reply = " ".join(sentences[:3])
            if reply[-1] not in '.!?':
                reply += '.'

        # Generate TTS
        audio_path, viseme_data = await controller.generate_speech(agent.name, reply)

        # Send to Unity
        await controller.ws_server.send_agent_response(
            agent_name=agent.name,
            text=reply,
            audio_path=audio_path,
            viseme_data=viseme_data,
            stance="neutral",
            turn=controller.speech_count
        )

        # Update state
        controller.last_speaker = agent.name
        controller.history.append({"agent": agent.name, "response": reply})
        controller.speech_count += 1

        # Log
        motivation_snapshot = {a.name: a.motivation_score for a in controller.agents}
        controller.logger.log_utterance(
            speaker=agent.name,
            content=reply,
            turn=controller.speech_count,
            is_qa=False,
            stance="neutral",
            motivation_scores=motivation_snapshot
        )

        print(f"[Summary] {agent.name}: {reply}\n")

        # Wait for audio
        if viseme_data:
            last_v = viseme_data[-1]
            audio_duration = last_v["time"] + last_v["duration"]
        else:
            audio_duration = max(2.0, len(reply.split()) / 2.5)
        sleep_remaining = audio_duration + 0.5
        while sleep_remaining > 0:
            await asyncio.sleep(min(0.5, sleep_remaining))
            sleep_remaining -= 0.5

    print("[Dialogue] Summary phase complete")


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
