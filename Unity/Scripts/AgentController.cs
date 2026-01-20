// AgentController.cs
// Controls individual agent character (animation, lip sync, highlighting)

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace PhilosophySalon
{
    public class AgentController : MonoBehaviour
    {
        [Header("Agent Info")]
        public string agentName;

        [Header("Visual Components")]
        public SkinnedMeshRenderer faceRenderer;
        public Animator animator;

        [Header("Highlight Effect")]
        public GameObject highlightEffect;
        public Light spotLight;
        public float highlightIntensity = 2f;
        public Color speakingColor = Color.yellow;
        public Color thinkingColor = Color.cyan;

        [Header("Animation Parameters")]
        public string idleState = "Idle";
        public string thinkingState = "Thinking";
        public string speakingState = "Speaking";

        [Header("Lip Sync - Blendshape Mapping")]
        [Tooltip("Maps viseme names to blendshape indices")]
        public VisemeBlendshapeMapping[] visemeMappings;

        [Header("Motivation Visual")]
        public Renderer motivationIndicator;
        public Color lowMotivationColor = Color.blue;
        public Color highMotivationColor = Color.red;

        private LipSyncController lipSyncController;
        private float currentMotivation = 0f;
        private AgentState currentState = AgentState.Idle;

        public enum AgentState
        {
            Idle,
            Thinking,
            Speaking
        }

        void Awake()
        {
            // Create lip sync controller
            lipSyncController = gameObject.AddComponent<LipSyncController>();
            lipSyncController.faceRenderer = faceRenderer;
            lipSyncController.visemeMappings = visemeMappings;
        }

        void Start()
        {
            SetIdle();
        }

        public void SetIdle()
        {
            currentState = AgentState.Idle;
            SetHighlight(false);

            if (animator != null)
            {
                animator.SetTrigger(idleState);
            }

            lipSyncController?.StopLipSync();
        }

        public void SetThinking()
        {
            currentState = AgentState.Thinking;
            SetHighlight(true, thinkingColor);

            if (animator != null)
            {
                animator.SetTrigger(thinkingState);
            }
        }

        public void SetSpeaking()
        {
            currentState = AgentState.Speaking;
            SetHighlight(true, speakingColor);

            if (animator != null)
            {
                animator.SetTrigger(speakingState);
            }
        }

        void SetHighlight(bool active, Color? color = null)
        {
            if (highlightEffect != null)
            {
                highlightEffect.SetActive(active);
            }

            if (spotLight != null)
            {
                spotLight.enabled = active;
                spotLight.intensity = active ? highlightIntensity : 0;

                if (color.HasValue)
                {
                    spotLight.color = color.Value;
                }
            }
        }

        public void PlayLipSync(VisemeEvent[] visemeData)
        {
            if (lipSyncController != null)
            {
                lipSyncController.PlayVisemeSequence(visemeData);
            }
        }

        public void StopLipSync()
        {
            if (lipSyncController != null)
            {
                lipSyncController.StopLipSync();
            }
        }

        public void SetMotivation(float value)
        {
            currentMotivation = Mathf.Clamp01(value);

            if (motivationIndicator != null)
            {
                Color color = Color.Lerp(lowMotivationColor, highMotivationColor, currentMotivation);
                motivationIndicator.material.color = color;
            }
        }

        public AgentState CurrentState => currentState;
        public float CurrentMotivation => currentMotivation;
    }

    [System.Serializable]
    public class VisemeBlendshapeMapping
    {
        public string visemeName; // e.g., "aa", "oh", "PP"
        public int blendshapeIndex; // Index in SkinnedMeshRenderer
        public float maxWeight = 100f; // Maximum blendshape weight
    }
}
