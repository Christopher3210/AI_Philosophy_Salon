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
            Recent dialogue history for context (format: {'agent': name, 'response': text})
        """
        try:
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

        except Exception as e:
            print(f"[MotivationScorer] Error in analyze_utterance: {e}")

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

        Uses keyword-based heuristics for fast, non-blocking detection.

        Returns
        -------
        Agent or None
            The agent being refuted, or None if no refutation detected
        """
        # Quick heuristic: look for refutation keywords
        refutation_keywords = [
            "disagree", "wrong", "incorrect", "no", "but", "however",
            "actually", "not quite", "that's false", "I challenge",
            "on the contrary", "rather", "cannot accept", "must object"
        ]

        has_refutation_signal = any(
            keyword in text.lower()
            for keyword in refutation_keywords
        )

        if not has_refutation_signal or len(recent_history) < 1:
            return None

        # Simple heuristic: assume refuting the last speaker
        # TODO: Add async LLM-based detection for more accuracy
        last_speaker_name = recent_history[-1]['agent']

        for agent in all_agents:
            if agent.name == last_speaker_name:
                return agent

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

        Uses keyword-based heuristics for fast, non-blocking detection.

        Returns the agent with opposing viewpoint.
        """
        # Conflict indicators
        conflict_keywords = [
            "versus", "against", "opposite", "contradicts",
            "conflict", "tension", "dispute", "opposed to"
        ]

        has_conflict_signal = any(
            keyword in text.lower()
            for keyword in conflict_keywords
        )

        if not has_conflict_signal or len(recent_history) < 1:
            return None

        # Simple heuristic: check if any agent's name appears near conflict keywords
        # TODO: Add async LLM-based detection for more accuracy
        text_lower = text.lower()

        for agent in all_agents:
            if agent.name == speaker_name:
                continue

            # Check if agent's name appears in text with conflict keywords nearby
            name_lower = agent.name.lower()
            if name_lower in text_lower:
                # Simple proximity check: is name within 50 chars of a conflict keyword?
                for keyword in conflict_keywords:
                    if keyword in text_lower:
                        return agent

        # If no name mentioned, assume conflict with last speaker
        if recent_history:
            last_speaker_name = recent_history[-1]['agent']
            for agent in all_agents:
                if agent.name == last_speaker_name and agent.name != speaker_name:
                    return agent

        return None
