// LipSyncController.cs
// Controls lip sync animation using blendshapes based on viseme data
// Supports Oculus/Meta standard 15 visemes

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace PhilosophySalon
{
    // Mapping structure for viseme to blendshape
    [System.Serializable]
    public class VisemeBlendshapeMapping
    {
        public string visemeName;      // Viseme ID from Azure (e.g., "aa", "sil")
        public string blendshapeName;  // BlendShape name in model (e.g., "viseme_aa")
        public int blendshapeIndex;    // Cached index for performance
        public float maxWeight = 100.0f; // Maximum weight (use 100.0 for 0-100 range models)
    }

    public class LipSyncController : MonoBehaviour
    {
        [Header("Face Mesh")]
        public SkinnedMeshRenderer faceRenderer;

        [Header("Viseme Mappings")]
        [Tooltip("Auto-populated on Awake if empty")]
        public VisemeBlendshapeMapping[] visemeMappings;

        [Header("Animation Settings")]
        [Range(0.01f, 0.2f)]
        public float blendSpeed = 0.1f;
        [Range(0f, 1f)]
        [Tooltip("Overall lip sync strength")]
        public float intensity = 1.0f;

        [Header("Audio Sync")]
        [Tooltip("Link to AudioSource for precise sync")]
        public AudioSource syncAudioSource;

        private Dictionary<string, VisemeBlendshapeMapping> visemeMap;
        private Coroutine currentLipSyncCoroutine;
        private bool isPlaying = false;

        // Track current blendshape weights for smooth transitions
        private Dictionary<int, float> currentWeights = new Dictionary<int, float>();

        // Oculus/Meta standard viseme names (matches Azure TTS output)
        // Azure outputs: sil, aa, O, E, I, U, nn, RR, kk, TH, FF, DD, SS
        // Model BlendShapes: viseme_sil, viseme_PP, viseme_FF, viseme_TH, viseme_DD,
        //                    viseme_kk, viseme_CH, viseme_SS, viseme_nn, viseme_RR,
        //                    viseme_aa, viseme_E, viseme_I, viseme_O, viseme_U
        private static readonly Dictionary<string, string> AZURE_TO_BLENDSHAPE = new Dictionary<string, string>
        {
            { "sil", "viseme_sil" },
            { "aa", "viseme_aa" },
            { "E", "viseme_E" },
            { "I", "viseme_I" },
            { "O", "viseme_O" },
            { "U", "viseme_U" },
            { "FF", "viseme_FF" },
            { "TH", "viseme_TH" },
            { "DD", "viseme_DD" },
            { "kk", "viseme_kk" },
            { "SS", "viseme_SS" },
            { "nn", "viseme_nn" },
            { "RR", "viseme_RR" },
            // These visemes may be triggered by certain phonemes
            { "PP", "viseme_PP" },  // bilabial plosives (p, b, m)
            { "CH", "viseme_CH" },  // affricates (ch, j)
        };

        void Awake()
        {
            BuildVisemeMap();
        }

        void BuildVisemeMap()
        {
            visemeMap = new Dictionary<string, VisemeBlendshapeMapping>();

            // If no mappings provided, auto-generate from standard Oculus visemes
            if (visemeMappings == null || visemeMappings.Length == 0)
            {
                AutoGenerateMappings();
            }

            // Build the lookup dictionary
            if (visemeMappings != null)
            {
                foreach (var mapping in visemeMappings)
                {
                    if (!string.IsNullOrEmpty(mapping.visemeName))
                    {
                        // Find blendshape index if not cached
                        if (mapping.blendshapeIndex < 0)
                        {
                            mapping.blendshapeIndex = FindBlendshapeIndexByName(mapping.blendshapeName);
                        }
                        visemeMap[mapping.visemeName] = mapping;
                    }
                }
            }

            Debug.Log($"[LipSync] Initialized with {visemeMap.Count} viseme mappings");
        }

        void AutoGenerateMappings()
        {
            if (faceRenderer == null || faceRenderer.sharedMesh == null)
            {
                Debug.LogWarning("[LipSync] Cannot auto-generate mappings: no face renderer");
                return;
            }

            var mappingList = new List<VisemeBlendshapeMapping>();

            foreach (var kvp in AZURE_TO_BLENDSHAPE)
            {
                string visemeName = kvp.Key;
                string blendshapeName = kvp.Value;

                int index = FindBlendshapeIndexByName(blendshapeName);
                if (index >= 0)
                {
                    mappingList.Add(new VisemeBlendshapeMapping
                    {
                        visemeName = visemeName,
                        blendshapeName = blendshapeName,
                        blendshapeIndex = index,
                        maxWeight = 100.0f  // For models with 0-100 BlendShape range
                    });
                    Debug.Log($"[LipSync] Mapped {visemeName} -> {blendshapeName} (index {index})");
                }
            }

            visemeMappings = mappingList.ToArray();
            Debug.Log($"[LipSync] Auto-generated {visemeMappings.Length} viseme mappings");
        }

        int FindBlendshapeIndexByName(string blendshapeName)
        {
            if (faceRenderer == null || faceRenderer.sharedMesh == null) return -1;

            Mesh mesh = faceRenderer.sharedMesh;
            for (int i = 0; i < mesh.blendShapeCount; i++)
            {
                if (mesh.GetBlendShapeName(i).Equals(blendshapeName, System.StringComparison.OrdinalIgnoreCase))
                {
                    return i;
                }
            }
            return -1;
        }

        public void PlayVisemeSequence(VisemeEvent[] visemeData)
        {
            if (faceRenderer == null)
            {
                Debug.LogWarning("[LipSync] No face renderer assigned");
                return;
            }

            if (visemeData == null || visemeData.Length == 0)
            {
                Debug.LogWarning("[LipSync] No viseme data provided");
                return;
            }

            // Stop any current lip sync
            StopLipSync();

            // Start new lip sync
            currentLipSyncCoroutine = StartCoroutine(PlayVisemeSequenceCoroutine(visemeData));
        }

        IEnumerator PlayVisemeSequenceCoroutine(VisemeEvent[] visemeData)
        {
            isPlaying = true;
            float startTime = Time.unscaledTime;  // Use unscaled time as fallback

            int currentIndex = 0;

            while (isPlaying && currentIndex < visemeData.Length)
            {
                // Use AudioSource.time for precise sync, fallback to elapsed time
                float elapsed;
                if (syncAudioSource != null && syncAudioSource.isPlaying)
                {
                    elapsed = syncAudioSource.time;
                }
                else
                {
                    elapsed = Time.unscaledTime - startTime;
                }

                // Process all visemes that should have started by now
                while (currentIndex < visemeData.Length && visemeData[currentIndex].time <= elapsed)
                {
                    ApplyViseme(visemeData[currentIndex]);
                    currentIndex++;
                }

                // Smooth blend existing weights
                UpdateBlendshapeWeights();

                yield return null;
            }

            // Reset to neutral
            ResetBlendshapes();
            isPlaying = false;
        }

        void ApplyViseme(VisemeEvent viseme)
        {
            if (string.IsNullOrEmpty(viseme.viseme)) return;

            // First, reset ALL viseme weights to 0 (only keep current viseme active)
            foreach (var kvp in visemeMap)
            {
                if (kvp.Value.blendshapeIndex >= 0)
                {
                    currentWeights[kvp.Value.blendshapeIndex] = 0f;
                }
            }

            // Now set the current viseme weight
            if (visemeMap.TryGetValue(viseme.viseme, out VisemeBlendshapeMapping mapping))
            {
                if (mapping.blendshapeIndex >= 0)
                {
                    float targetWeight = mapping.maxWeight * viseme.weight * intensity;
                    currentWeights[mapping.blendshapeIndex] = targetWeight;
                }
            }
            else
            {
                // Fallback: Try to find blendshape directly
                string blendshapeName = "viseme_" + viseme.viseme;
                int index = FindBlendshapeIndexByName(blendshapeName);

                if (index < 0)
                {
                    index = FindBlendshapeIndexByName(viseme.viseme);
                }

                if (index >= 0)
                {
                    float targetWeight = 100.0f * viseme.weight * intensity;
                    currentWeights[index] = targetWeight;

                    // Cache this mapping
                    var newMapping = new VisemeBlendshapeMapping
                    {
                        visemeName = viseme.viseme,
                        blendshapeName = blendshapeName,
                        blendshapeIndex = index,
                        maxWeight = 100.0f
                    };
                    visemeMap[viseme.viseme] = newMapping;
                }
            }

        }

        void SetTargetWeight(int index, float weight)
        {
            currentWeights[index] = weight;
        }

        void UpdateBlendshapeWeights()
        {
            if (faceRenderer == null) return;

            foreach (var kvp in currentWeights)
            {
                int index = kvp.Key;
                float targetWeight = kvp.Value;

                if (index >= 0 && index < faceRenderer.sharedMesh.blendShapeCount)
                {
                    float currentWeight = faceRenderer.GetBlendShapeWeight(index);
                    float newWeight = Mathf.Lerp(currentWeight, targetWeight, blendSpeed);
                    faceRenderer.SetBlendShapeWeight(index, newWeight);
                }
            }

            // Decay weights that aren't being actively set
            for (int i = 0; i < faceRenderer.sharedMesh.blendShapeCount; i++)
            {
                if (!currentWeights.ContainsKey(i))
                {
                    float currentWeight = faceRenderer.GetBlendShapeWeight(i);
                    if (currentWeight > 0.1f)
                    {
                        float newWeight = Mathf.Lerp(currentWeight, 0, blendSpeed);
                        faceRenderer.SetBlendShapeWeight(i, newWeight);
                    }
                }
            }
        }

        public void StopLipSync()
        {
            isPlaying = false;

            if (currentLipSyncCoroutine != null)
            {
                StopCoroutine(currentLipSyncCoroutine);
                currentLipSyncCoroutine = null;
            }

            ResetBlendshapes();
        }

        void ResetBlendshapes()
        {
            if (faceRenderer == null) return;

            currentWeights.Clear();

            // Reset all blendshapes to 0
            for (int i = 0; i < faceRenderer.sharedMesh.blendShapeCount; i++)
            {
                faceRenderer.SetBlendShapeWeight(i, 0);
            }
        }

        public bool IsPlaying => isPlaying;

        // Debug method to list all blendshapes
        [ContextMenu("List Blendshapes")]
        public void ListBlendshapes()
        {
            if (faceRenderer == null || faceRenderer.sharedMesh == null)
            {
                Debug.Log("No face renderer or mesh assigned");
                return;
            }

            Mesh mesh = faceRenderer.sharedMesh;
            Debug.Log($"Blendshapes ({mesh.blendShapeCount}):");

            for (int i = 0; i < mesh.blendShapeCount; i++)
            {
                Debug.Log($"  [{i}] {mesh.GetBlendShapeName(i)}");
            }
        }
    }
}
