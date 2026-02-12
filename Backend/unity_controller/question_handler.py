# unity_controller/question_handler.py
# Handles user questions during dialogue

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


async def handle_question(controller: 'UnityDialogueController', question: str, target_agents: list = None):
    """
    Handle a question from Unity.
    Supports pause/interrupt between and during answers.

    Parameters
    ----------
    controller : UnityDialogueController
        The main controller
    question : str
        The user's question
    target_agents : list, optional
        List of agent names selected by user to answer
    """
    # Cancel main loop immediately to prevent any new speakers
    if controller.main_loop_task and not controller.main_loop_task.done():
        controller.main_loop_task.cancel()
        try:
            await controller.main_loop_task
        except asyncio.CancelledError:
            pass
        controller.main_loop_task = None

    controller.is_answering_question = True
    controller.is_paused = False
    controller.was_interrupted = False

    try:
        # Use user-selected agents
        if target_agents:
            responding_agents = [a for a in controller.agents if a.name in target_agents]
            print(f"[Unity] Selected responders: {', '.join(a.name for a in responding_agents)}")
        else:
            responding_agents = controller.agents
            print(f"[Unity] No agents selected, all philosophers will respond")

        # Each responding agent answers
        for agent in responding_agents:
            # Check if paused between answerers
            # Pause: is_paused=True, was_interrupted=False → wait here
            # After interrupt+continue: is_paused=False → skip this check
            if controller.is_paused and not controller.was_interrupted:
                print(f"[Unity] Q&A paused before {agent.name} - waiting for resume")
                await controller.ws_server.send_event("paused", {})
                while controller.is_paused and not controller.should_stop:
                    await asyncio.sleep(0.1)
                if controller.should_stop:
                    break

            await _generate_answer(controller, agent, question)

            if controller.should_stop:
                break

        # After all responses, stay paused and notify Unity
        print("[Unity] Question answered - showing pause panel again")
        controller.is_paused = True
        controller.was_interrupted = False
        await controller.ws_server.send_event("paused", {})

    finally:
        controller.is_answering_question = False


async def _generate_answer(controller: 'UnityDialogueController', agent, question: str):
    """Generate and send an answer from a specific agent."""
    print(f"[Unity] {agent.name} responding to question...")

    # Notify Unity
    await controller.ws_server.send_agent_speaking(agent.name, controller.last_speaker)

    # Build context
    context = controller.build_context()
    context_block = f"Recent dialogue:\n{context}\n\n" if context else ""
    topic_block = f"Debate topic: {controller.current_topic}\n\n" if controller.current_topic else ""

    # Generate response
    user_prompt = (
        f"{topic_block}"
        f"{context_block}"
        f"A participant asks: {question}\n\n"
        f"Answer this question directly in 1-3 concise sentences.\n"
        f"- Speak in first person using 'I'\n"
        f"- Do NOT introduce yourself\n"
        f"- Jump straight to your answer"
    )

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

    # Generate TTS and viseme data
    audio_path, viseme_data = await controller.generate_speech(agent.name, reply, is_qa=True)

    # Send to Unity
    await controller.ws_server.send_agent_response(
        agent_name=agent.name,
        text=reply,
        audio_path=audio_path,
        viseme_data=viseme_data,
        stance="neutral",
        turn=controller.speech_count
    )

    # Wait for audio to finish - check for interrupt during wait
    words = len(reply.split())
    estimated_duration = max(2.0, words / 2.5)
    print(f"[Unity] Waiting {estimated_duration:.1f}s for {agent.name} to finish speaking...")

    sleep_remaining = estimated_duration
    while sleep_remaining > 0:
        await asyncio.sleep(min(0.5, sleep_remaining))
        sleep_remaining -= 0.5

        # Interrupt: stop waiting immediately (frontend already paused audio)
        if controller.was_interrupted:
            print(f"[Unity] {agent.name} interrupted during audio wait")
            # Wait for resume
            while controller.is_paused and not controller.should_stop:
                await asyncio.sleep(0.1)
            if controller.should_stop:
                return
            print(f"[Unity] Resumed after interrupt - continuing Q&A")
            break

    # Update history
    controller.last_speaker = agent.name
    controller.history.append({"agent": agent.name, "response": reply})
    controller.speech_count += 1
