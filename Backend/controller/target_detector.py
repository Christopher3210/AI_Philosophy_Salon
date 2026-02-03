# controller/target_detector.py
# Detects which philosophers should respond to a question

import re
from typing import List, Optional


class TargetDetector:
    """
    Detects which philosophers should respond to a question.

    Supports:
    - Direct addressing (e.g., "hello aristotle", "aristotle, what...")
    - Exclusion patterns (e.g., "except aristotle", "everyone but sartre")
    - Multiple targets (e.g., "aristotle and russell")
    - LLM-based detection for ambiguous cases
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
        question_lower = question.lower()

        # Get last speaker from history for context
        last_speaker = None
        if recent_history and len(recent_history) > 0:
            last_speaker = recent_history[-1].get('agent')

        # 1. Check for "everyone/all" patterns
        everyone_keywords = ['everyone', 'everybody', 'all of you', 'you all']
        has_everyone = any(keyword in question_lower for keyword in everyone_keywords)

        if not has_everyone:
            if ' all ' in question_lower or question_lower.startswith('all ') or question_lower.endswith(' all'):
                has_everyone = True

        if has_everyone:
            return self._handle_everyone_pattern(question_lower, last_speaker)

        # 2. Check for standalone exclusion patterns
        if last_speaker:
            targets = self._check_standalone_exclusion(question_lower, last_speaker)
            if targets:
                return targets

        # 3. Check for "[Name]'s idea/opinion" pattern
        targets = self._check_opinion_pattern(question_lower)
        if targets:
            return targets

        # 4. Check for trailing address (e.g., "..., aristotle?")
        addressed_name = self._find_trailing_address(question_lower)
        if addressed_name:
            print(f"[Target Detection] Trailing address detected: {addressed_name}")
            return [addressed_name]

        # 5. Use LLM for ambiguous cases
        if self.model_manager:
            targets = self._llm_based_detection(question, last_speaker=last_speaker)
            if targets is not None:
                return targets

        # Fallback: all respond
        return []

    def _handle_everyone_pattern(self, question_lower: str, last_speaker: str) -> List[str]:
        """Handle 'everyone/all' patterns with possible exclusions."""
        # Check for explicit exclusions
        if 'except' in question_lower or ' but ' in question_lower:
            excluded_names = []
            for agent in self.agents:
                if agent.name.lower() in question_lower:
                    excluded_names.append(agent.name)

            if excluded_names:
                targets = [a.name for a in self.agents if a.name not in excluded_names]
                print(f"[Target Detection] Everyone except {', '.join(excluded_names)} → {', '.join(targets)}")
                return targets

        # Check for contextual exclusions
        if last_speaker and any(kw in question_lower for kw in ['else', 'other', 'rest']):
            targets = [a.name for a in self.agents if a.name != last_speaker]
            print(f"[Target Detection] Everyone except {last_speaker} → {', '.join(targets)}")
            return targets

        print(f"[Target Detection] Everyone")
        return []

    def _check_standalone_exclusion(self, question_lower: str, last_speaker: str) -> Optional[List[str]]:
        """Check for standalone exclusion patterns like 'the rest', 'the others'."""
        patterns = ['the rest', 'the others']

        for pattern in patterns:
            if pattern in question_lower:
                targets = [a.name for a in self.agents if a.name != last_speaker]
                print(f"[Target Detection] '{pattern}' → Everyone except {last_speaker}")
                return targets

        # Check 'others' with word boundary
        if re.search(r'\bothers\b', question_lower):
            targets = [a.name for a in self.agents if a.name != last_speaker]
            print(f"[Target Detection] 'others' → Everyone except {last_speaker}")
            return targets

        return None

    def _check_opinion_pattern(self, question_lower: str) -> Optional[List[str]]:
        """Check for '[Name]'s idea/opinion' pattern."""
        opinion_keywords = ["'s idea", "'s opinion", "'s view", "'s perspective", "'s argument", "'s point"]

        for keyword in opinion_keywords:
            if keyword in question_lower:
                discussed_names = []
                for agent in self.agents:
                    possessive = agent.name.lower() + keyword
                    if possessive in question_lower:
                        discussed_names.append(agent.name)

                if discussed_names:
                    # Check if there's a trailing address
                    addressed_name = self._find_trailing_address(question_lower)
                    if addressed_name:
                        print(f"[Target Detection] Asking {addressed_name} about {', '.join(discussed_names)}'s idea")
                        return [addressed_name]
                    else:
                        targets = [a.name for a in self.agents if a.name not in discussed_names]
                        print(f"[Target Detection] About {', '.join(discussed_names)}'s idea → {', '.join(targets)}")
                        return targets

        return None

    def _find_trailing_address(self, question_lower: str) -> Optional[str]:
        """Find trailing address like '..., aristotle?'"""
        patterns = [
            r',\s*(\w+)\s*[?!.]?\s*$',
            r'\s+(\w+)\s*[?!.]?\s*$',
        ]

        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                potential_name = match.group(1)

                # Exact match
                for agent in self.agents:
                    if agent.name.lower() == potential_name:
                        return agent.name

                # Fuzzy match (starts with, min 4 chars)
                for agent in self.agents:
                    if agent.name.lower().startswith(potential_name) and len(potential_name) >= 4:
                        return agent.name

        return None

    def _llm_based_detection(self, question: str, last_speaker: str = None) -> Optional[List[str]]:
        """Use LLM to detect who should respond."""
        agent_names = [a.name for a in self.agents]
        names_str = ", ".join(agent_names)

        context_info = ""
        if last_speaker:
            context_info = f"\n\nContext: {last_speaker} just spoke."
            context_info += f"\n- 'you' or 'your' refers to {last_speaker}"

        prompt = f"""Analyze who should respond to this question in a philosophical debate.

Question: "{question}"

Available philosophers: {names_str}{context_info}

Instructions:
- If "everyone", "all", or "everybody" is mentioned, list ALL philosophers
- If asking "you/your", respond with only the last speaker's name
- If specific philosophers are named, list only those names

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

            targets = []
            for agent in self.agents:
                if agent.name.lower() in response.lower():
                    targets.append(agent.name)

            if len(targets) == len(self.agents):
                print(f"[Target Detection] Everyone responds")
                return []

            if targets:
                print(f"[Target Detection] Specific targets: {', '.join(targets)}")
                return targets

            return []

        except Exception as e:
            print(f"[TargetDetector] LLM detection failed: {e}")
            return []
