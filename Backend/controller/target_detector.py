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

        Uses keyword matching for obvious cases, LLM for ambiguous ones.

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
        question_lower = question.lower()

        # Get last speaker from history for context
        last_speaker = None
        if recent_history and len(recent_history) > 0:
            last_speaker = recent_history[-1].get('agent')

        # 1. Check for "everyone/all" patterns
        everyone_keywords = ['everyone', 'everybody', 'all of you', 'you all']
        # Also check for standalone "all" (but be careful with "all of" vs just "all")
        has_everyone = any(keyword in question_lower for keyword in everyone_keywords)
        if not has_everyone and ' all ' in question_lower or question_lower.startswith('all ') or question_lower.endswith(' all'):
            has_everyone = True

        if has_everyone:
            # Check for explicit exclusions: "except [name]" or "but [name]"
            if 'except' in question_lower or ' but ' in question_lower:
                # Extract excluded names directly from question
                excluded_names = []
                for agent in self.agents:
                    if agent.name.lower() in question_lower:
                        excluded_names.append(agent.name)

                if excluded_names:
                    # Do exclusion directly in code (reliable)
                    targets = [a.name for a in self.agents if a.name not in excluded_names]
                    print(f"[Target Detection] Keyword match: Everyone except {', '.join(excluded_names)} → {', '.join(targets)}")
                    return targets
                else:
                    # "except/but" without specific name, treat as everyone
                    print(f"[Target Detection] Keyword match: Everyone")
                    return []
            # Check for contextual exclusions: "else", "others", "rest"
            elif last_speaker and any(kw in question_lower for kw in ['else', 'other', 'rest']):
                targets = [a.name for a in self.agents if a.name != last_speaker]
                print(f"[Target Detection] Keyword match: Everyone except {last_speaker} → {', '.join(targets)}")
                return targets
            else:
                print(f"[Target Detection] Keyword match: Everyone")
                return []  # Empty list = everyone

        # 2. Check for standalone exclusion patterns (without "everyone/all")
        # "the rest", "the others", "others" - exclude last speaker
        standalone_exclusion_patterns = [
            ('the rest', 'the rest'),
            ('the others', 'the others'),
            (r'\bothers\b', 'others'),  # word boundary to avoid "mothers", "brothers"
        ]

        if last_speaker:
            for pattern, display_name in standalone_exclusion_patterns:
                if pattern.startswith(r'\b'):  # regex pattern
                    import re
                    if re.search(pattern, question_lower):
                        targets = [a.name for a in self.agents if a.name != last_speaker]
                        print(f"[Target Detection] Keyword match: '{display_name}' → Everyone except {last_speaker} → {', '.join(targets)}")
                        return targets
                else:  # simple string match
                    if pattern in question_lower:
                        targets = [a.name for a in self.agents if a.name != last_speaker]
                        print(f"[Target Detection] Keyword match: '{display_name}' → Everyone except {last_speaker} → {', '.join(targets)}")
                        return targets

        # 3. Use LLM for ambiguous cases (specific names, pronouns, etc.)
        if self.model_manager:
            targets = self._llm_based_detection(question, last_speaker=last_speaker)
            if targets is not None:
                return targets

        # Fallback: all respond if detection fails
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
            context_info += f"\n- 'you' or 'your' refers to {last_speaker}"
            context_info += f"\n- If the question says 'others', 'everyone else', or 'rest', exclude {last_speaker}"

        prompt = f"""Analyze who should respond to this question in a philosophical debate.

Question: "{question}"

Available philosophers: {names_str}{context_info}

Instructions:
- If the question contains "everyone", "all", or "everybody", list ALL philosophers: {names_str}
- If asking "you/your" (which refers to the last speaker), respond with only the last speaker's name
- If asking "what do you think about [Person X]'s opinion/view/idea", respond with the last speaker's name (NOT Person X)
- If specific philosophers are directly named (e.g., "Russell, what..."), list only those names
- Consider pronouns and conversational context

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
