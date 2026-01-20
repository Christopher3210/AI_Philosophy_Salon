# viseme_generator.py
# Generate viseme (mouth shape) data from text for lip sync

import re
from typing import List, Dict, Any


class VisemeGenerator:
    """
    Generate viseme timing data from text for lip synchronization.

    Visemes are visual representations of phonemes (speech sounds).
    This generator creates a timeline of mouth shapes that Unity can use
    to animate character faces during speech.

    Standard Viseme Set (based on Oculus/Meta Lipsync):
    - sil: Silence (mouth closed)
    - PP: P, B, M sounds
    - FF: F, V sounds
    - TH: Th sounds
    - DD: T, D sounds
    - kk: K, G sounds
    - CH: Ch, J, Sh sounds
    - SS: S, Z sounds
    - nn: N, L sounds
    - RR: R sounds
    - aa: A sound (open mouth)
    - E: E sound
    - ih: I sound
    - oh: O sound
    - ou: U sound
    """

    # Mapping from characters/phonemes to visemes
    CHAR_TO_VISEME = {
        # Bilabial (lips together)
        'p': 'PP', 'b': 'PP', 'm': 'PP',

        # Labiodental (teeth on lip)
        'f': 'FF', 'v': 'FF',

        # Dental
        # 'th' handled separately

        # Alveolar
        't': 'DD', 'd': 'DD',

        # Velar
        'k': 'kk', 'g': 'kk', 'c': 'kk', 'q': 'kk',

        # Palato-alveolar
        # 'ch', 'sh', 'j' handled separately
        's': 'SS', 'z': 'SS',

        # Nasal/Lateral
        'n': 'nn', 'l': 'nn',

        # Rhotic
        'r': 'RR',

        # Vowels
        'a': 'aa',
        'e': 'E',
        'i': 'ih',
        'o': 'oh',
        'u': 'ou',

        # Semi-vowels
        'w': 'ou',
        'y': 'ih',
        'h': 'sil',

        # Default
        'x': 'kk',
    }

    # Digraphs and special patterns
    DIGRAPH_TO_VISEME = {
        'th': 'TH',
        'ch': 'CH',
        'sh': 'CH',
        'ph': 'FF',
        'wh': 'ou',
        'ng': 'kk',
        'ck': 'kk',
    }

    def __init__(self, words_per_minute: float = 150):
        """
        Initialize the viseme generator.

        Parameters
        ----------
        words_per_minute : float
            Speaking rate (default: 150 WPM, typical for speech)
        """
        self.wpm = words_per_minute
        # Average word length in English is about 5 characters
        # This gives us characters per second
        self.chars_per_second = (words_per_minute * 5) / 60

    def generate_visemes(self, text: str, audio_duration: float = None) -> List[Dict[str, Any]]:
        """
        Generate viseme timeline from text.

        Parameters
        ----------
        text : str
            The text to generate visemes for
        audio_duration : float, optional
            If provided, scale timing to match audio duration

        Returns
        -------
        List[Dict[str, Any]]
            List of viseme events:
            [{"time": float, "viseme": str, "weight": float, "duration": float}, ...]
        """
        if not text:
            return []

        # Clean text
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation

        viseme_events = []
        current_time = 0.0

        # Process text character by character
        i = 0
        while i < len(text):
            char = text[i]

            # Check for digraphs first
            if i < len(text) - 1:
                digraph = text[i:i+2]
                if digraph in self.DIGRAPH_TO_VISEME:
                    viseme = self.DIGRAPH_TO_VISEME[digraph]
                    duration = self._get_viseme_duration(viseme)

                    viseme_events.append({
                        "time": round(current_time, 3),
                        "viseme": viseme,
                        "weight": 1.0,
                        "duration": round(duration, 3)
                    })

                    current_time += duration
                    i += 2
                    continue

            # Handle single characters
            if char == ' ':
                # Short pause for word boundaries
                pause_duration = 0.05
                viseme_events.append({
                    "time": round(current_time, 3),
                    "viseme": "sil",
                    "weight": 0.5,
                    "duration": round(pause_duration, 3)
                })
                current_time += pause_duration
            elif char in self.CHAR_TO_VISEME:
                viseme = self.CHAR_TO_VISEME[char]
                duration = self._get_viseme_duration(viseme)

                viseme_events.append({
                    "time": round(current_time, 3),
                    "viseme": viseme,
                    "weight": 1.0,
                    "duration": round(duration, 3)
                })

                current_time += duration
            else:
                # Unknown character, treat as short silence
                current_time += 0.02

            i += 1

        # Scale timing if audio duration is provided
        if audio_duration and viseme_events and current_time > 0:
            scale_factor = audio_duration / current_time
            for event in viseme_events:
                event["time"] = round(event["time"] * scale_factor, 3)
                event["duration"] = round(event["duration"] * scale_factor, 3)

        return viseme_events

    def _get_viseme_duration(self, viseme: str) -> float:
        """
        Get the typical duration for a viseme.

        Parameters
        ----------
        viseme : str
            The viseme type

        Returns
        -------
        float
            Duration in seconds
        """
        # Base duration (seconds per character at current WPM)
        base_duration = 1.0 / self.chars_per_second

        # Adjust duration based on viseme type
        duration_multipliers = {
            'sil': 0.5,  # Silence is short
            'PP': 0.8,   # Plosives are quick
            'FF': 1.0,
            'TH': 1.2,   # Fricatives can be longer
            'DD': 0.8,
            'kk': 0.8,
            'CH': 1.0,
            'SS': 1.2,
            'nn': 1.0,
            'RR': 1.0,
            'aa': 1.5,   # Vowels are longer
            'E': 1.3,
            'ih': 1.2,
            'oh': 1.4,
            'ou': 1.4,
        }

        multiplier = duration_multipliers.get(viseme, 1.0)
        return base_duration * multiplier

    def get_viseme_for_blendshape_mapping(self) -> Dict[str, List[str]]:
        """
        Get mapping from visemes to typical blendshape names.

        This helps Unity know which blendshapes to activate for each viseme.

        Returns
        -------
        Dict[str, List[str]]
            Mapping from viseme to blendshape names
        """
        return {
            "sil": ["mouthClose"],
            "PP": ["mouthPucker", "mouthClose"],
            "FF": ["mouthFunnel", "jawOpen_0.1"],
            "TH": ["tongueOut", "jawOpen_0.2"],
            "DD": ["jawOpen_0.3", "mouthClose"],
            "kk": ["jawOpen_0.3", "mouthOpen"],
            "CH": ["mouthShrugUpper", "jawOpen_0.3"],
            "SS": ["mouthSmile", "jawOpen_0.2"],
            "nn": ["mouthClose", "jawOpen_0.2"],
            "RR": ["mouthPucker_0.5", "jawOpen_0.3"],
            "aa": ["jawOpen_0.7", "mouthOpen"],
            "E": ["mouthSmile", "jawOpen_0.4"],
            "ih": ["mouthSmile", "jawOpen_0.3"],
            "oh": ["mouthFunnel", "jawOpen_0.5"],
            "ou": ["mouthPucker", "jawOpen_0.4"],
        }


# Convenience function
def generate_viseme_data(text: str, audio_duration: float = None) -> List[Dict[str, Any]]:
    """
    Generate viseme data from text.

    Parameters
    ----------
    text : str
        The text to generate visemes for
    audio_duration : float, optional
        If provided, scale timing to match audio duration

    Returns
    -------
    List[Dict[str, Any]]
        List of viseme events
    """
    generator = VisemeGenerator()
    return generator.generate_visemes(text, audio_duration)
