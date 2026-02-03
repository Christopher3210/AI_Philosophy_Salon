# unity_controller/question_handler.py
# Handles user questions during dialogue

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


async def handle_question(controller: 'UnityDialogueController', question: str):
    """
    Handle a question from Unity using TargetDetector.

    Parameters
    ----------
    controller : UnityDialogueController
        The main controller
    question : str
        The user's question
    """
    # Cancel main loop immediately to prevent any new speakers
    if controller.main_loop_task and not controller.main_loop_task.done():
        controller.main_loop_task.cancel()
        try:
            await controller.main_loop_task
        except asyncio.CancelledError:
            pass

    controller.is_answering_question = True
    controller.is_paused = True

    # Detect who should respond
    target_names = controller.target_detector.detect_targets(
        question,
        recent_history=controller.history
    )

    if target_names:
        responding_agents = [a for a in controller.agents if a.name in target_names]
        print(f"[Unity] Target detected: {', '.join(target_names)}")
    else:
        responding_agents = controller.agents
        print(f"[Unity] No specific target, all philosophers will respond")

    # Each responding agent answers
    for agent in responding_agents:
        await _generate_answer(controller, agent, question)

    # After all responses, stay paused and notify Unity
    print("[Unity] Question answered - showing pause panel again")
    controller.is_answering_question = False
    controller.is_paused = True
    await controller.ws_server.send_event("paused", {})


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

    # Wait for audio to finish
    words = len(reply.split())
    estimated_duration = max(2.0, words / 2.5)
    print(f"[Unity] Waiting {estimated_duration:.1f}s for {agent.name} to finish speaking...")
    await asyncio.sleep(estimated_duration)

    # Update history
    controller.last_speaker = agent.name
    controller.history.append({"agent": agent.name, "response": reply})
    controller.speech_count += 1
