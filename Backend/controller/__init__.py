# controller/__init__.py

from .dialogue_controller import DialogueController

# For backwards compatibility
TurnTakingController = DialogueController

__all__ = ['DialogueController', 'TurnTakingController']
