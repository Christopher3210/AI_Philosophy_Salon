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

    def __init__(self, agents):
        """
        Parameters
        ----------
        agents : list
            List of Agent objects
        """
        self.agents = agents

    def detect_targets(self, question: str) -> List[str]:
        """
        Detect which philosophers should respond to the question.

        Parameters
        ----------
        question : str
            The user's question

        Returns
        -------
        list of str
            List of agent names that should respond, or empty list if all should respond
        """
        question_lower = question.lower()

        # Priority 1: Check for exclusion patterns
        excluded = self._check_exclusion_patterns(question_lower)
        if excluded:
            return excluded

        # Priority 2: Check for "others" pattern (all philosophers)
        if self._check_others_pattern(question_lower):
            return []  # Empty list means everyone responds

        # Priority 3: Direct address with greeting
        targets = self._check_greeting_patterns(question_lower)
        if targets:
            return targets

        # Priority 4: Name at start with comma/colon
        targets = self._check_name_first_pattern(question_lower)
        if targets:
            return targets

        # Priority 5: Trailing address
        targets = self._check_trailing_address(question_lower)
        if targets:
            return targets

        # Priority 6: Single mention in question
        targets = self._check_single_mention(question_lower)
        if targets:
            return targets

        # Default: all respond
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
