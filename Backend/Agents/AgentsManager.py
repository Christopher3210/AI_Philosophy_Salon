
class AgentsManager:
    def __init__(self):
        self.agents = {
            "aristotle": {
                "system": (
                    "You are Aristotle. You speak briefly, calmly, logically, using simple"
                    " philosophical terms. Respond in 1-3 short sentences."
                )
            },
            "russell": {
                "system": (
                    "You are Bertrand Russell. You speak in a direct, skeptical, analytic style."
                    " Challenge assumptions. Respond in 1-3 sharp sentences."
                )
            }
        }

    def get_system_prompt(self, agent_name: str):
        """Return the system prompt for a given agent."""
        return self.agents[agent_name]["system"]