# controller/target_detector.py
# Uses LLM to intelligently detect which philosophers should respond

from typing import List, Optional


class TargetDetector:
    """
    Uses LLM to detect which philosophers should respond to a question.

    Much smarter than keyword-based detection - can understand context,
    pronouns, implicit references, and complex phrasings.
    """

    def __init__(self, agents, model_manager):
        """
        Parameters
        ----------
        agents : list
            List of Agent objects
        model_manager : ModelManager
            Required for LLM-based detection
        """
        self.agents = agents
        self.model_manager = model_manager

    def detect_targets(self, question: str, recent_history: List = None) -> List[str]:
        """
        Use LLM to detect which philosophers should respond.

        Parameters
        ----------
        question : str
            The user's question
        recent_history : list, optional
            Recent dialogue history for context

        Returns
        -------
        list of str
            List of agent names that should respond, or empty list if all should respond
        """
        agent_names = [a.name for a in self.agents]

        # Build context from recent history
        context_lines = []
        if recent_history:
            for item in recent_history[-5:]:  # Last 5 exchanges
                speaker = item.get('agent', 'Unknown')
                response = item.get('response', '')
                # Truncate long responses
                if len(response) > 100:
                    response = response[:100] + "..."
                context_lines.append(f"{speaker}: {response}")

        context_str = "\n".join(context_lines) if context_lines else "No previous dialogue."

        # Get last speaker
        last_speaker = None
        if recent_history and len(recent_history) > 0:
            last_speaker = recent_history[-1].get('agent')

        # Build the prompt
        prompt = self._build_prompt(question, agent_names, context_str, last_speaker)

        try:
            response = self.model_manager.chat_once(
                model_key="mistral",
                system_prompt=self._get_system_prompt(),
                user_prompt=prompt,
                max_new_tokens=50,
                temperature=0.1
            )

            return self._parse_response(response, agent_names)

        except Exception as e:
            print(f"[TargetDetector] LLM error: {e}, defaulting to all")
            return []

    def _get_system_prompt(self) -> str:
        """System prompt for the LLM."""
        return """You are an assistant that analyzes questions in a philosophical debate.
Your task is to determine which philosophers should respond to a given question.
You must respond with ONLY a comma-separated list of philosopher names, nothing else.
If everyone should respond, respond with "ALL".
Be precise and follow the instructions carefully."""

    def _build_prompt(self, question: str, agent_names: List[str], context: str, last_speaker: str) -> str:
        """Build the analysis prompt."""
        names_str = ", ".join(agent_names)

        prompt = f"""Analyze this question and determine who should respond.

Available philosophers: {names_str}

Recent dialogue context:
{context}

The last speaker was: {last_speaker if last_speaker else "None (this is the first question)"}

Question from user: "{question}"

Rules:
1. If the question mentions specific philosopher names, only those philosophers should respond
2. If the question uses "you" or "your", it refers to the last speaker ({last_speaker})
3. If the question asks about someone's "idea/opinion/view/argument", everyone EXCEPT that person should respond
4. If the question says "everyone", "all", "everybody", then ALL should respond
5. If the question says "others", "the rest", "everyone else", then everyone EXCEPT the last speaker should respond
6. If the question is general (no specific target), ALL should respond
7. Names might be misspelled or abbreviated - match the closest philosopher name

Who should respond? Reply with ONLY the names (comma-separated) or "ALL":"""

        return prompt

    def _parse_response(self, response: str, agent_names: List[str]) -> List[str]:
        """Parse LLM response to extract philosopher names."""
        response = response.strip().upper()

        # Check for "ALL" response
        if response == "ALL" or "ALL" in response.split():
            print(f"[Target Detection] LLM says: ALL respond")
            return []

        # Extract names from response
        response_lower = response.lower()
        targets = []

        for name in agent_names:
            if name.lower() in response_lower:
                targets.append(name)

        if targets:
            print(f"[Target Detection] LLM detected: {', '.join(targets)}")
            return targets

        # If no names found but not "ALL", default to all
        print(f"[Target Detection] LLM response unclear: '{response}', defaulting to ALL")
        return []
