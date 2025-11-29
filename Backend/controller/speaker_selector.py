# controller/speaker_selector.py

import random
from typing import List, Dict, Any


class SpeakerSelector:
    """
    Selects the next speaker in a free-form dialogue.

    Uses weighted random selection combining:
    - Anti-monopoly mechanism (reduce weight for recent speakers)
    - Event-driven motivation scores (refutation, name mention, conflict, silence)
    - Random factor for natural unpredictability
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

        Combines anti-monopoly weights with event-driven motivation scores
        for more natural debate dynamics.

        Returns
        -------
        Agent
            The selected agent to speak next
        """
        # First speaker: completely random
        if not self.history:
            selected = random.choice(self.agents)
            selected.turns_since_last_speech = 0
            return selected

        # Track recent speakers (last 3 utterances)
        recent_speakers = [item['agent'] for item in self.history[-3:]]

        # Calculate combined weights for each agent
        weights = []
        for agent in self.agents:
            # 1. Anti-monopoly weight (prevent one agent from dominating)
            recent_count = recent_speakers.count(agent.name)
            anti_monopoly_weight = max(1, 5 - recent_count * 2)

            # 2. Motivation score (event-driven: refutation, mention, conflict, silence)
            motivation_factor = 1.0 + agent.motivation_score

            # 3. Combined weight
            final_weight = anti_monopoly_weight * motivation_factor
            weights.append(final_weight)

        # Weighted random selection
        selected = random.choices(self.agents, weights=weights, k=1)[0]

        # Reset selected agent's motivation score after being chosen
        selected.motivation_score = 0.0
        selected.turns_since_last_speech = 0

        return selected
