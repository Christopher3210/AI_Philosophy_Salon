# unity_controller/dialogue_loop.py
# Main dialogue loop for Unity mode

import asyncio
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


async def run_dialogue_loop(controller: 'UnityDialogueController'):
    """
    Main dialogue loop - can be cancelled and restarted.

    Parameters
    ----------
    controller : UnityDialogueController
        The main controller instance
    """
    topic = controller.dialogue_topic

    while not controller.should_stop:
        # Check if paused at start of each iteration
        if controller.is_paused:
            print("[Dialogue] Paused - sending notification to Unity")
            await controller.ws_server.send_event("paused", {})
            # Wait until resumed
            while controller.is_paused and not controller.should_stop:
                await asyncio.sleep(0.1)
            if controller.should_stop:
                break
            print("[Dialogue] Resumed - continuing loop")
            continue

        if controller.is_answering_question:
            await asyncio.sleep(0.1)
            continue

        # Select speaker: resume same speaker after interrupt, honour invite override, otherwise next
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

        # Notify Unity that agent is thinking (with last speaker for Look At)
        await controller.ws_server.send_agent_speaking(speaker.name, controller.last_speaker)
        print(f"\n{speaker.name} is thinking...")

        # Analyze stance
        stance = controller.stance_analyzer.analyze_stance(
            agent=speaker,
            recent_history=controller.history[-3:],
            conviviality=controller.conviviality
        )

        # Get tone instruction
        tone_instruction = controller.stance_analyzer.get_tone_instruction(
            stance=stance,
            conviviality=controller.conviviality
        )

        # Build context and prompt
        context = controller.build_context()
        context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

        # Build optional instructions with probability to avoid repetition
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

        # Add direct engagement instruction if there was a previous speaker
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

        # Generate response
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

        # Clean speaker name from reply
        reply = _clean_reply(reply, speaker.name)

        # Trim to target sentence count (find Nth sentence boundary, cut there)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', reply.strip())
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > target_sentences:
            reply = " ".join(sentences[:target_sentences])
            if reply[-1] not in '.!?':
                reply += '.'

        # Detect if this reply invites a specific philosopher to respond next
        controller.next_speaker_override = _detect_invited_speaker(reply, other_names)

        # Generate TTS audio and viseme data
        audio_path, viseme_data = await controller.generate_speech(speaker.name, reply)

        # Send response to Unity
        await controller.ws_server.send_agent_response(
            agent_name=speaker.name,
            text=reply,
            audio_path=audio_path,
            viseme_data=viseme_data,
            stance=stance,
            turn=controller.speech_count
        )

        # Update local state
        controller.last_speaker = speaker.name
        speaker.add_memory(user_prompt, reply)
        controller.history.append({"agent": speaker.name, "response": reply})
        controller.speech_count += 1

        # Log utterance
        motivation_snapshot = {agent.name: agent.motivation_score for agent in controller.agents}
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

        # Send updated motivation scores to Unity
        motivation_scores = {agent.name: agent.motivation_score for agent in controller.agents}
        await controller.ws_server.send_motivation_update(motivation_scores)

        print(f"[{speaker.name}] {reply}\n")

        # Wait for audio to finish playing before next turn
        words = len(reply.split())
        estimated_duration = max(2.0, words / 2.5)
        thinking_pause = 0.5
        total_wait = estimated_duration + thinking_pause
        print(f"[Dialogue] Waiting {total_wait:.1f}s (audio: {estimated_duration:.1f}s + pause: {thinking_pause:.1f}s)")

        # Use short sleep intervals so we can be cancelled quickly
        # Do NOT break on is_paused here — Pause should wait for audio to finish.
        # Interrupt uses task.cancel() which raises CancelledError directly.
        sleep_remaining = total_wait
        while sleep_remaining > 0:
            await asyncio.sleep(min(0.5, sleep_remaining))
            sleep_remaining -= 0.5

    print("[Dialogue] Main loop ended normally")


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
    # Only look at the last sentence
    sentences = [s.strip() for s in reply.replace('?', '?.').split('.') if s.strip()]
    last = sentences[-1] if sentences else ""
    for name in other_names:
        if name in last:
            return name
    return None
