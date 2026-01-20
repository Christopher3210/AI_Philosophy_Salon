// LipSyncController.cs
// Controls lip sync animation using blendshapes based on viseme data

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace PhilosophySalon
{
    public class LipSyncController : MonoBehaviour
    {
        [Header("Face Mesh")]
        public SkinnedMeshRenderer faceRenderer;

        [Header("Viseme Mappings")]
        public VisemeBlendshapeMapping[] visemeMappings;

        [Header("Animation Settings")]
        [Range(0.01f, 0.2f)]
        public float blendSpeed = 0.1f;
        [Range(0f, 1f)]
        public float intensity = 1f;

        private Dictionary<string, VisemeBlendshapeMapping> visemeMap;
        private Coroutine currentLipSyncCoroutine;
        private bool isPlaying = false;

        // Track current blendshape weights for smooth transitions
        private Dictionary<int, float> currentWeights = new Dictionary<int, float>();

        void Awake()
        {
            BuildVisemeMap();
        }

        void BuildVisemeMap()
        {
            visemeMap = new Dictionary<string, VisemeBlendshapeMapping>();

            if (visemeMappings != null)
            {
                foreach (var mapping in visemeMappings)
                {
                    if (!string.IsNullOrEmpty(mapping.visemeName))
                    {
                        visemeMap[mapping.visemeName] = mapping;
                    }
                }
            }

            // Add default mappings if none provided
            if (visemeMap.Count == 0)
            {
                Debug.LogWarning("[LipSync] No viseme mappings provided. Using default search.");
            }
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
            float startTime = Time.time;

            int currentIndex = 0;

            while (isPlaying && currentIndex < visemeData.Length)
            {
                float elapsed = Time.time - startTime;

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

            // Try to find mapping
            if (visemeMap.TryGetValue(viseme.viseme, out VisemeBlendshapeMapping mapping))
            {
                float targetWeight = mapping.maxWeight * viseme.weight * intensity;
                SetTargetWeight(mapping.blendshapeIndex, targetWeight);
            }
            else
            {
                // Try to find blendshape by name
                int index = FindBlendshapeIndex(viseme.viseme);
                if (index >= 0)
                {
                    float targetWeight = 100f * viseme.weight * intensity;
                    SetTargetWeight(index, targetWeight);
                }
            }
        }

        int FindBlendshapeIndex(string visemeName)
        {
            if (faceRenderer == null || faceRenderer.sharedMesh == null) return -1;

            Mesh mesh = faceRenderer.sharedMesh;

            // Try exact match first
            for (int i = 0; i < mesh.blendShapeCount; i++)
            {
                string shapeName = mesh.GetBlendShapeName(i);
                if (shapeName.Equals(visemeName, System.StringComparison.OrdinalIgnoreCase))
                {
                    return i;
                }
            }

            // Try partial match
            string searchTerm = GetBlendshapeSearchTerm(visemeName);
            for (int i = 0; i < mesh.blendShapeCount; i++)
            {
                string shapeName = mesh.GetBlendShapeName(i).ToLower();
                if (shapeName.Contains(searchTerm))
                {
                    return i;
                }
            }

            return -1;
        }

        string GetBlendshapeSearchTerm(string visemeName)
        {
            // Map viseme names to common blendshape naming conventions
            switch (visemeName.ToLower())
            {
                case "aa": return "jaw"; // or "mouth_open"
                case "oh": return "funnel"; // or "mouth_o"
                case "ou": return "pucker";
                case "e": return "smile";
                case "ih": return "smile";
                case "pp": return "close"; // or "mouth_close"
                case "ff": return "funnel";
                case "th": return "tongue";
                case "dd": return "jaw";
                case "kk": return "open";
                case "ch": return "shrug";
                case "ss": return "smile";
                case "nn": return "close";
                case "rr": return "pucker";
                case "sil": return "close";
                default: return visemeName.ToLower();
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
