# controller/__init__.py
# Core dialogue control modules

from .speaker_selector import SpeakerSelector
from .stance_analyzer import StanceAnalyzer
from .motivation_scorer import MotivationScorer
from .target_detector import TargetDetector
from .debate_logger import DebateLogger

__all__ = [
    'SpeakerSelector',
    'StanceAnalyzer',
    'MotivationScorer',
    'TargetDetector',
    'DebateLogger',
]
