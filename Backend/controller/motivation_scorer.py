# controller/motivation_scorer.py

import random
import re
from typing import List, Optional
from agents.agent_base import Agent


class MotivationScorer:
    """
    Event-driven motivation scoring system for natural debate dynamics.

    Tracks various events (refutation, name mention, conflict, silence)
    and updates each agent's motivation score accordingly.
    """

    # Scoring rules (can be tuned)
    SCORE_REFUTED = 3.0          # When someone's view is challenged
    SCORE_NAME_MENTIONED = 2.0   # When someone's name is mentioned
    SCORE_PER_SILENT_TURN = 0.5  # Accumulated per turn of silence
    SCORE_CONFLICT = 3.0         # When strong semantic conflict detected
    RANDOM_RANGE = (0.0, 1.0)    # Random factor for unpredictability

    def __init__(self, model_manager):
        """
        Parameters
        ----------
        model_manager : ModelManager
            Used for lightweight LLM-based event detection
        """
        self.model_manager = model_manager

    def analyze_utterance(
        self,
        speaker_name: str,
        text: str,
        all_agents: List[Agent],
        recent_history: List[dict]
    ):
        """
        Analyze a new utterance and update all agents' motivation scores.

        Parameters
        ----------
        speaker_name : str
            Name of the agent who just spoke
        text : str
            The utterance content
        all_agents : list of Agent
            All participating agents
        recent_history : list of dict
            Recent dialogue history for context
        """
        # 1. Detect if someone's view was refuted
        refuted_agent = self._detect_refutation(text, all_agents, recent_history)
        if refuted_agent:
            refuted_agent.motivation_score += self.SCORE_REFUTED

        # 2. Detect name mentions
        for agent in all_agents:
            if agent.name != speaker_name and self._is_name_mentioned(agent.name, text):
                agent.motivation_score += self.SCORE_NAME_MENTIONED

        # 3. Detect strong conflict (opposing viewpoint)
        opponent = self._detect_conflict(speaker_name, text, all_agents, recent_history)
        if opponent:
            opponent.motivation_score += self.SCORE_CONFLICT

        # 4. Update silence counters and add silence motivation
        for agent in all_agents:
            if agent.name == speaker_name:
                agent.turns_since_last_speech = 0
            else:
                agent.turns_since_last_speech += 1
                # Gradual motivation increase for silent agents
                agent.motivation_score += self.SCORE_PER_SILENT_TURN

        # 5. Add random factor to all agents for unpredictability
        for agent in all_agents:
            agent.motivation_score += random.uniform(*self.RANDOM_RANGE)

    def _is_name_mentioned(self, agent_name: str, text: str) -> bool:
        """
        Check if an agent's name appears in the text.

        Uses case-insensitive matching.
        """
        return agent_name.lower() in text.lower()

    def _detect_refutation(
        self,
        text: str,
        all_agents: List[Agent],
        recent_history: List[dict]
    ) -> Optional[Agent]:
        """
        Detect if this utterance refutes someone's previous statement.

        Uses LLM-based semantic analysis for accuracy.

        Returns
        -------
        Agent or None
            The agent being refuted, or None if no refutation detected
        """
        # Quick heuristic: look for refutation keywords
        refutation_keywords = [
            "disagree", "wrong", "incorrect", "no", "but", "however",
            "actually", "not quite", "that's false", "I challenge",
            "on the contrary", "rather"
        ]

        has_refutation_signal = any(
            keyword in text.lower()
            for keyword in refutation_keywords
        )

        if not has_refutation_signal or len(recent_history) < 1:
            return None

        # Use LLM to detect who is being refuted
        # Build context from last 2 turns
        context = ""
        for item in recent_history[-2:]:
            context += f"{item['agent']}: {item['text']}\n"

        agent_names = [a.name for a in all_agents]

        prompt = f"""Analyze if this statement refutes or challenges any philosopher's view.

Recent context:
{context}

New statement: "{text}"

If it refutes someone, reply with ONLY their name from: {', '.join(agent_names)}
If no refutation, reply with: none

Reply:"""

        try:
            # Use lightweight detection (low temperature, few tokens)
            response = self.model_manager.chat_once(
                model_key="mistral",
                system_prompt="You are a debate analyzer. Respond concisely.",
                user_prompt=prompt,
                max_new_tokens=10,
                temperature=0.3
            )

            response = response.strip().lower()

            # Find matching agent
            for agent in all_agents:
                if agent.name.lower() in response:
                    return agent

        except Exception as e:
            print(f"[MotivationScorer] Refutation detection failed: {e}")

        return None

    def _detect_conflict(
        self,
        speaker_name: str,
        text: str,
        all_agents: List[Agent],
        recent_history: List[dict]
    ) -> Optional[Agent]:
        """
        Detect if there's strong semantic conflict with another agent.

        Returns the agent with opposing viewpoint.
        """
        # Conflict indicators
        conflict_keywords = [
            "versus", "against", "opposite", "contradicts",
            "conflict", "tension", "dispute"
        ]

        has_conflict_signal = any(
            keyword in text.lower()
            for keyword in conflict_keywords
        )

        if not has_conflict_signal or len(recent_history) < 1:
            return None

        # Build recent context
        context = ""
        for item in recent_history[-3:]:
            if item['agent'] != speaker_name:
                context += f"{item['agent']}: {item['text']}\n"

        if not context:
            return None

        agent_names = [a.name for a in all_agents if a.name != speaker_name]

        prompt = f"""Does this statement strongly oppose someone's viewpoint?

Recent statements:
{context}

New statement: "{text}"

If it opposes someone, reply with ONLY their name from: {', '.join(agent_names)}
If no strong opposition, reply with: none

Reply:"""

        try:
            response = self.model_manager.chat_once(
                model_key="mistral",
                system_prompt="You are a debate analyzer. Respond concisely.",
                user_prompt=prompt,
                max_new_tokens=10,
                temperature=0.3
            )

            response = response.strip().lower()

            # Find matching agent
            for agent in all_agents:
                if agent.name != speaker_name and agent.name.lower() in response:
                    return agent

        except Exception as e:
            print(f"[MotivationScorer] Conflict detection failed: {e}")

        return None
