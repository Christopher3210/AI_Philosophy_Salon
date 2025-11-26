# agents/agents_manager.py

import os
import yaml
from .agent_base import Agent


class AgentsManager:
    """
    Dynamically loads all philosophical agents from YAML config files.

    Each YAML file describes one agent (name, model_key, voice, system prompt).
    """

    def __init__(self, cfg_dir: str = os.path.join("agents", "configs")):
        self.agents: dict[str, Agent] = {}
        self._load_configs(cfg_dir)

    def _load_configs(self, cfg_dir: str):
        """
        Read all *.yaml files in cfg_dir and create Agent objects.
        """
        if not os.path.isdir(cfg_dir):
            raise FileNotFoundError(f"Agents config directory not found: {cfg_dir}")

        for file in sorted(os.listdir(cfg_dir)):
            if not file.lower().endswith(".yaml"):
                continue

            path = os.path.join(cfg_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)

            name = cfg["name"]
            system_prompt = cfg["system"]
            model_key = cfg["model_key"]
            voice = cfg.get("voice")

            agent = Agent(
                name=name,
                system_prompt=system_prompt,
                model_key=model_key,
                voice=voice,
            )
            # Use lowercase key for robust lookup
            self.agents[name.lower()] = agent

        if not self.agents:
            raise RuntimeError("No agents loaded. Please add YAML configs in agents/configs/.")

    def get(self, name: str) -> Agent | None:
        """
        Return an Agent by (case-insensitive) name.
        """
        return self.agents.get(name.lower())

    def get_all_agents(self) -> list[Agent]:
        """
        Return all agents in a deterministic order.
        Currently sorted by name; you can change this if needed.
        """
        # If you want custom order, you could add "order" field in YAML.
        return [self.agents[k] for k in sorted(self.agents.keys())]

    def list_names(self) -> list[str]:
        """
        Return all agent names.
        """
        return [agent.name for agent in self.get_all_agents()]
