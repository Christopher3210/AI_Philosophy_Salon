# unity_controller/dialogue_loop.py
# Main dialogue loop — pipelined pre-computation: LLM during audio, TTS right after

import asyncio
import random
import re
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


async def run_dialogue_loop(controller: 'UnityDialogueController'):
    """
    Main dialogue loop with pipelined pre-computation.

    During current speaker's audio:
      - LLM for next turn runs (fast, ~3s, always finishes in time)
    When audio finishes:
      - Camera moves to next speaker (thinking animation)
      - TTS generates (~5-10s, user sees natural thinking)
      - Next speaker starts talking

    First turn has full delay (LLM + TTS). Subsequent turns only wait for TTS.
    """
    topic = controller.dialogue_topic
    llm_prefetch = None  # Pre-computed LLM result (text, no audio)

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

        # ── Get turn data (full prefetch with TTS, or LLM-only, or fresh) ──
        if llm_prefetch and 'audio_path' in llm_prefetch:
            # Full prefetch: LLM + TTS already done
            llm_data = llm_prefetch
            audio_path = llm_data['audio_path']
            viseme_data = llm_data['viseme_data']
            llm_prefetch = None
            print(f"[Dialogue] Using fully pre-computed turn for {llm_data['speaker'].name}")
            # Camera transition
            await controller.ws_server.send_agent_speaking(llm_data['speaker'].name, controller.last_speaker)
            await asyncio.sleep(0.5)
        else:
            # LLM only or fresh — need to generate TTS
            if llm_prefetch:
                llm_data = llm_prefetch
                llm_prefetch = None
                print(f"[Dialogue] Using pre-computed LLM for {llm_data['speaker'].name}")
            else:
                llm_data = await _generate_llm(controller, topic)

            # Show thinking + generate TTS
            await controller.ws_server.send_agent_speaking(llm_data['speaker'].name, controller.last_speaker)
            print(f"[Dialogue] Generating TTS for {llm_data['speaker'].name}...")
            audio_path, viseme_data = await controller.generate_speech(llm_data['speaker'].name, llm_data['reply'])

        speaker = llm_data['speaker']
        reply = llm_data['reply']
        stance = llm_data['stance']
        other_names = llm_data['other_names']

        # ── Send response — audio starts playing ──
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

        motivation_snapshot = {a.name: a.motivation_score for a in controller.agents}
        controller.logger.log_utterance(
            speaker=speaker.name,
            content=reply,
            turn=controller.speech_count,
            is_qa=False,
            stance=stance,
            motivation_scores=motivation_snapshot
        )

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

        # ── Check time before pre-computing ──
        if _is_time_up(controller):
            if viseme_data:
                last = viseme_data[-1]
                audio_duration = last["time"] + last["duration"]
            else:
                audio_duration = max(2.0, len(reply.split()) / 2.5)
            sleep_remaining = audio_duration + 0.5
            while sleep_remaining > 0:
                await asyncio.sleep(min(0.5, sleep_remaining))
                sleep_remaining -= 0.5
            print("[Dialogue] Time is up — entering summary phase")
            await _run_summary_phase(controller, topic)
            controller.should_stop = True
            break

        # ── Start full prefetch (LLM + TTS) during audio ──
        controller.prefetch_task = asyncio.create_task(
            _generate_full_turn(controller, topic)
        )

        # ── Wait for audio ──
        if viseme_data:
            last = viseme_data[-1]
            audio_duration = last["time"] + last["duration"]
        else:
            audio_duration = max(2.0, len(reply.split()) / 2.5)

        # Accumulate actual speaking time for debate timer
        controller.debate_elapsed += audio_duration
        elapsed_str = f"{controller.debate_elapsed:.0f}s"
        limit_str = f"{controller.debate_duration}s" if controller.debate_duration > 0 else "∞"

        thinking_pause = 0.5
        total_wait = audio_duration + thinking_pause
        print(f"[Dialogue] Waiting {total_wait:.1f}s for audio ({elapsed_str}/{limit_str}), pre-computing next turn...")

        sleep_remaining = total_wait
        while sleep_remaining > 0:
            await asyncio.sleep(min(0.5, sleep_remaining))
            sleep_remaining -= 0.5

        # ── Collect full prefetch ──
        full_prefetch = None
        if controller.prefetch_task and not controller.prefetch_task.cancelled():
            try:
                if controller.prefetch_task.done():
                    full_prefetch = controller.prefetch_task.result()
                    print(f"[Dialogue] Pre-computation ready: {full_prefetch['speaker'].name}")
                else:
                    # Not ready — play a filler clip while waiting
                    filler_speaker = getattr(controller, '_prefetch_speaker', None)
                    filler = controller.tts.get_filler(filler_speaker) if filler_speaker else None

                    if filler:
                        print(f"[Dialogue] Playing filler for {filler_speaker} while waiting...")
                        await controller.ws_server.send_agent_speaking(filler_speaker, controller.last_speaker)
                        await controller.ws_server.send_agent_response(
                            agent_name=filler_speaker,
                            text=filler["text"],
                            audio_path=filler["audio_path"],
                            viseme_data=filler["viseme_data"],
                            stance="neutral",
                            turn=controller.speech_count
                        )
                        # Wait for filler audio, break early if prefetch done or cancelled
                        if filler["viseme_data"]:
                            filler_last = filler["viseme_data"][-1]
                            filler_dur = filler_last["time"] + filler_last["duration"]
                        else:
                            filler_dur = 2.0
                        filler_remaining = filler_dur
                        while filler_remaining > 0:
                            task = controller.prefetch_task
                            if task is None or task.done() or task.cancelled():
                                break
                            if controller.is_paused or controller.should_stop:
                                break
                            await asyncio.sleep(min(0.5, filler_remaining))
                            filler_remaining -= 0.5

                    # Check if task was cancelled by pause/interrupt
                    task = controller.prefetch_task
                    if task is None or task.cancelled():
                        full_prefetch = None
                    else:
                        if not task.done():
                            print("[Dialogue] Waiting for pre-computation to finish...")
                        full_prefetch = await task
                    print(f"[Dialogue] Pre-computation complete: {full_prefetch['speaker'].name}")
            except asyncio.CancelledError:
                full_prefetch = None
            except Exception as e:
                print(f"[Dialogue] Pre-computation error: {e}")
                full_prefetch = None

        controller.prefetch_task = None

        # If full prefetch succeeded, use it (skip TTS next iteration)
        if full_prefetch:
            llm_prefetch = full_prefetch
        else:
            llm_prefetch = None

    print("[Dialogue] Main loop ended normally")


async def _generate_full_turn(controller: 'UnityDialogueController', topic: str) -> dict:
    """Generate complete turn: LLM + TTS. Used for pre-computation during audio."""
    t0 = time.time()
    llm_data = await _generate_llm(controller, topic)
    t1 = time.time()
    # Store the selected speaker so filler can match
    controller._prefetch_speaker = llm_data['speaker'].name
    print(f"[Prefetch] LLM done in {t1-t0:.1f}s for {llm_data['speaker'].name} ({len(llm_data['reply'])} chars)")

    audio_path, viseme_data = await controller.generate_speech(
        llm_data['speaker'].name, llm_data['reply']
    )
    t2 = time.time()
    print(f"[Prefetch] TTS done in {t2-t1:.1f}s, total prefetch: {t2-t0:.1f}s")

    return {**llm_data, 'audio_path': audio_path, 'viseme_data': viseme_data}


async def _generate_llm(controller: 'UnityDialogueController', topic: str) -> dict:
    """Generate LLM response only (no TTS). Fast enough to finish during audio."""
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

    # Hard character limit to prevent super-long compound sentences
    max_chars = 120 if target_sentences == 1 else 300
    if len(reply) > max_chars:
        # Cut at last sentence boundary within limit
        truncated = reply[:max_chars]
        last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        if last_period > 30:
            reply = truncated[:last_period + 1]
        else:
            # Cut at last comma or semicolon for a natural pause
            last_comma = max(truncated.rfind(','), truncated.rfind(';'))
            if last_comma > 30:
                reply = truncated[:last_comma] + '.'
            else:
                last_space = truncated.rfind(' ')
                if last_space > 30:
                    reply = truncated[:last_space] + '.'

    return {
        'speaker': speaker,
        'reply': reply,
        'stance': stance,
        'other_names': other_names,
        'user_prompt': user_prompt,
    }


def _is_time_up(controller: 'UnityDialogueController') -> bool:
    if controller.debate_duration <= 0:
        return False
    return controller.debate_elapsed >= controller.debate_duration


async def _run_summary_phase(controller: 'UnityDialogueController', topic: str):
    print("\n" + "=" * 50)
    print("  SUMMARY PHASE")
    print("=" * 50)

    agent_statements = {}
    for agent in controller.agents:
        own = [h["response"] for h in controller.history if h["agent"] == agent.name]
        agent_statements[agent.name] = own

    for agent in controller.agents:
        if controller.should_stop:
            break

        own_statements = agent_statements.get(agent.name, [])
        if own_statements:
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

        await controller.ws_server.send_agent_speaking(agent.name, controller.last_speaker)

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

        sentences = re.split(r'(?<=[.!?])\s+', reply.strip())
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > 3:
            reply = " ".join(sentences[:3])
            if reply[-1] not in '.!?':
                reply += '.'

        audio_path, viseme_data = await controller.generate_speech(agent.name, reply)

        await controller.ws_server.send_agent_response(
            agent_name=agent.name,
            text=reply,
            audio_path=audio_path,
            viseme_data=viseme_data,
            stance="neutral",
            turn=controller.speech_count
        )

        controller.last_speaker = agent.name
        controller.history.append({"agent": agent.name, "response": reply})
        controller.speech_count += 1

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
    if reply.startswith(speaker_name + ":"):
        reply = reply[len(speaker_name) + 1:].strip()
    elif reply.startswith(speaker_name):
        reply = reply[len(speaker_name):].strip()
        if reply.startswith(":"):
            reply = reply[1:].strip()
    return reply


def _detect_invited_speaker(reply: str, other_names: list) -> str | None:
    if '?' not in reply:
        return None
    sentences = [s.strip() for s in reply.replace('?', '?.').split('.') if s.strip()]
    last = sentences[-1] if sentences else ""
    for name in other_names:
        if name in last:
            return name
    return None
