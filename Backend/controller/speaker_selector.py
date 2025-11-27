# controller/speaker_selector.py

import random
from typing import List, Dict, Any


class SpeakerSelector:
    """
    Selects the next speaker in a free-form dialogue.

    Uses weighted random selection to:
    - Prevent monopolization (reduce weight for recent speakers)
    - Maintain natural conversation flow
    - Allow for future enhancements (LLM-based desire scoring)
    """

    def __init__(self, agents, history: List[Dict[str, Any]]):
        """
        Parameters
        ----------
        agents : list
            List of Agent objects
        history : list
            Dialogue history (shared reference)
        """
        self.agents = agents
        self.history = history

    def select_next_speaker(self):
        """
        Select the next speaker based on weighted random selection.

        Returns
        -------
        Agent
            The selected agent to speak next
        """
        # First speaker: completely random
        if not self.history:
            return random.choice(self.agents)

        # Track recent speakers (last 3 utterances)
        recent_speakers = [item['agent'] for item in self.history[-3:]]

        # Calculate weights for each agent
        weights = []
        for agent in self.agents:
            recent_count = recent_speakers.count(agent.name)
            # Weight formula: max(1, 5 - count * 2)
            # More recent speeches = lower weight
            weight = max(1, 5 - recent_count * 2)
            weights.append(weight)

        # Weighted random selection
        return random.choices(self.agents, weights=weights, k=1)[0]
