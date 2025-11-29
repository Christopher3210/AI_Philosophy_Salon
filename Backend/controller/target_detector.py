# controller/target_detector.py

import re
from typing import List


class TargetDetector:
    """
    Detects which philosophers should respond to a question.

    Supports:
    - Direct addressing (e.g., "hello aristotle", "aristotle, what...")
    - Exclusion patterns (e.g., "except aristotle", "everyone but sartre")
    - Multiple targets (e.g., "aristotle and russell")
    """

    def __init__(self, agents, model_manager=None):
        """
        Parameters
        ----------
        agents : list
            List of Agent objects
        model_manager : ModelManager, optional
            For LLM-based intelligent target detection
        """
        self.agents = agents
        self.model_manager = model_manager

    def detect_targets(self, question: str, recent_history: List = None) -> List[str]:
        """
        Detect which philosophers should respond to the question.

        Uses LLM-based intelligent detection for accurate semantic understanding.

        Parameters
        ----------
        question : str
            The user's question
        recent_history : list, optional
            Recent dialogue history to provide context (e.g., who just spoke)

        Returns
        -------
        list of str
            List of agent names that should respond, or empty list if all should respond
        """
        # Get last speaker from history for context
        last_speaker = None
        if recent_history and len(recent_history) > 0:
            last_speaker = recent_history[-1].get('agent')

        # Use LLM for all target detection
        if self.model_manager:
            targets = self._llm_based_detection(question, last_speaker=last_speaker)
            if targets is not None:
                return targets

        # Fallback: all respond if LLM detection fails
        return []

    def _check_others_pattern(self, question_lower: str) -> bool:
        """Check for 'others' pattern indicating all should respond."""
        others_patterns = [
            r'\bother[s\']?\b',      # others, other's, other
            r'\beveryone\b',          # everyone
            r'\ball\b',              # all
            r'\brest\b',             # rest
            r'\beverybody\b',        # everybody
        ]
        return any(re.search(pattern, question_lower) for pattern in others_patterns)

    def _check_exclusion_patterns(self, question_lower: str) -> List[str]:
        """Check for exclusion patterns like 'except aristotle'."""
        exclusion_patterns = [
            r'except\s+(\w+)',
            r'not\s+(\w+)',
            r'everyone\s+(?:but|except)\s+(\w+)',
            r'all\s+(?:but|except)\s+(\w+)',
        ]

        for pattern in exclusion_patterns:
            match = re.search(pattern, question_lower)
            if match:
                excluded_name = match.group(1)
                # Return all agents except the excluded one
                excluded_agents = []
                for agent in self.agents:
                    if agent.name.lower() != excluded_name:
                        excluded_agents.append(agent.name)
                # Only return if we found a valid exclusion
                if len(excluded_agents) < len(self.agents):
                    return excluded_agents
        return []

    def _check_greeting_patterns(self, question_lower: str) -> List[str]:
        """Check for greeting + name patterns like 'hello aristotle'."""
        pattern = r'^(?:hey|hi|hello|greetings)\s+(\w+)(?:\s+and\s+(\w+))?'
        match = re.match(pattern, question_lower)

        if match:
            addressed = [name for name in match.groups() if name]
            targets = []
            for agent in self.agents:
                if agent.name.lower() in addressed:
                    targets.append(agent.name)
            return targets
        return []

    def _check_name_first_pattern(self, question_lower: str) -> List[str]:
        """Check for name at start with comma/colon like 'aristotle, what...'."""
        pattern = r'^(\w+)(?:\s+and\s+(\w+))?(?:\s*,|\s*:)'
        match = re.match(pattern, question_lower)

        if match:
            addressed = [name for name in match.groups() if name]
            targets = []
            for agent in self.agents:
                if agent.name.lower() in addressed:
                    targets.append(agent.name)
            return targets
        return []

    def _check_trailing_address(self, question_lower: str) -> List[str]:
        """Check for trailing address like 'what do you think, aristotle?'."""
        pattern = r',\s*(\w+)\s*[?!.]?$'
        match = re.search(pattern, question_lower)

        if match:
            addressed_name = match.group(1)
            for agent in self.agents:
                if agent.name.lower() == addressed_name:
                    return [agent.name]
        return []

    def _check_single_mention(self, question_lower: str) -> List[str]:
        """Check if only one philosopher is mentioned in a direct question."""
        # Find all mentioned philosophers
        mentioned = []
        for agent in self.agents:
            name_lower = agent.name.lower()
            if re.search(r'\b' + re.escape(name_lower) + r'\b', question_lower):
                mentioned.append(agent.name)

        # If only one mentioned and starts with question word
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'should']
        starts_with_question = any(question_lower.strip().startswith(qw) for qw in question_words)

        if len(mentioned) == 1 and starts_with_question:
            # Return the single mentioned philosopher as target
            return mentioned

        return []

    def _llm_based_detection(self, question: str, last_speaker: str = None) -> List[str] | None:
        """
        Use LLM to intelligently detect who should respond.

        Returns
        -------
        list of str or None
            List of agent names, empty list for all, or None if detection failed
        """
        agent_names = [a.name for a in self.agents]
        names_str = ", ".join(agent_names)

        context_info = ""
        if last_speaker:
            context_info = f"\n\nContext: {last_speaker} just spoke."
            context_info += f"\n- If the question says 'others', 'everyone else', or 'rest', exclude {last_speaker} from your response."

        prompt = f"""Analyze who should respond to this question in a philosophical debate.

Question: "{question}"

Available philosophers: {names_str}{context_info}

Instructions:
- Reply with the comma-separated names of philosophers who should respond
- If everyone should respond, list all their names
- If specific philosophers are addressed, list only those names
- Consider direct addressing, pronouns like 'you', and contextual references

Reply with ONLY the names (comma-separated):"""

        try:
            response = self.model_manager.chat_once(
                model_key="mistral",
                system_prompt="You are a debate analyzer. Respond with only comma-separated philosopher names.",
                user_prompt=prompt,
                max_new_tokens=30,
                temperature=0.1
            )

            response = response.strip()
            print(f"[Target Detection] LLM response: '{response}'")

            # Extract names mentioned in response
            targets = []
            for agent in self.agents:
                if agent.name.lower() in response.lower():
                    targets.append(agent.name)

            # If all philosophers mentioned, return empty list (everyone responds)
            if len(targets) == len(self.agents):
                print(f"[Target Detection] Everyone responds")
                return []

            if targets:
                print(f"[Target Detection] Specific targets: {', '.join(targets)}")
                return targets
            else:
                print(f"[Target Detection] Could not parse response, defaulting to everyone")
                return []

        except Exception as e:
            print(f"[TargetDetector] LLM detection failed: {e}")
            return []
