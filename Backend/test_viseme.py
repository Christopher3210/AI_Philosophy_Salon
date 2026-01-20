# test_viseme.py
# Test the viseme generator independently

import json
from unity_bridge import generate_viseme_data, VisemeGenerator

def test_viseme_generator():
    """Test viseme generation with sample text."""

    print("=" * 50)
    print("  Viseme Generator Test")
    print("=" * 50)

    # Test texts
    test_texts = [
        "Hello, how are you?",
        "Freedom is the absence of constraint.",
        "I disagree with your position on ethics.",
        "The meaning of life is complex.",
    ]

    generator = VisemeGenerator()

    for text in test_texts:
        print(f"\n📝 Text: \"{text}\"")
        print("-" * 40)

        # Generate visemes
        visemes = generator.generate_visemes(text)

        print(f"   Generated {len(visemes)} viseme events")
        print(f"   Duration: {visemes[-1]['time'] + visemes[-1]['duration']:.2f}s" if visemes else "   No visemes")

        # Show first 10 visemes
        print("\n   First 10 visemes:")
        for v in visemes[:10]:
            print(f"     {v['time']:5.2f}s | {v['viseme']:4s} | weight: {v['weight']:.1f} | dur: {v['duration']:.3f}s")

        if len(visemes) > 10:
            print(f"     ... and {len(visemes) - 10} more")

    # Test with audio duration scaling
    print("\n" + "=" * 50)
    print("  Testing with Audio Duration Scaling")
    print("=" * 50)

    text = "This is a test sentence for timing."
    audio_duration = 3.0  # 3 seconds

    visemes_unscaled = generator.generate_visemes(text)
    visemes_scaled = generator.generate_visemes(text, audio_duration=audio_duration)

    print(f"\n📝 Text: \"{text}\"")
    print(f"   Unscaled duration: {visemes_unscaled[-1]['time'] + visemes_unscaled[-1]['duration']:.2f}s")
    print(f"   Scaled to: {audio_duration}s")
    print(f"   Scaled duration: {visemes_scaled[-1]['time'] + visemes_scaled[-1]['duration']:.2f}s")

    # Show blendshape mapping
    print("\n" + "=" * 50)
    print("  Viseme to Blendshape Mapping")
    print("=" * 50)

    mapping = generator.get_viseme_for_blendshape_mapping()
    for viseme, blendshapes in mapping.items():
        print(f"   {viseme:4s} -> {', '.join(blendshapes)}")

    print("\n✅ Viseme generator test completed!")

    # Output sample JSON
    print("\n" + "=" * 50)
    print("  Sample JSON Output")
    print("=" * 50)

    sample_visemes = generate_viseme_data("Hello world", audio_duration=1.5)
    print(json.dumps(sample_visemes[:5], indent=2))


if __name__ == "__main__":
    test_viseme_generator()
