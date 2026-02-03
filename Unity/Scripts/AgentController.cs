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

        [Header("Animation - Idle States")]
        [Tooltip("Multiple idle animation state names (randomly selected)")]
        public string[] idleAnimations = { "Idle", "Breathing Idle", "Standing Idle" };

        [Header("Animation - Thinking States")]
        [Tooltip("Multiple thinking animation state names (randomly selected)")]
        public string[] thinkingAnimations = { "Thinking" };

        [Header("Animation - Speaking States")]
        [Tooltip("Multiple speaking animation state names (randomly selected)")]
        public string[] speakingAnimations = { "Talking", "Talking1", "Talking2" };

        [Header("Animation - Gesture Animations")]
        [Tooltip("Optional gesture animations that can play during speaking")]
        public string[] gestureAnimations = { "HeadNod", "Dismissing", "AnnoyedShake" };
        [Range(0f, 1f)]
        public float gestureChance = 0.3f;  // 30% chance to add gesture

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
        private Coroutine gestureCoroutine;

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

        /// <summary>
        /// Select a random animation from an array
        /// </summary>
        private string GetRandomAnimation(string[] animations)
        {
            if (animations == null || animations.Length == 0)
                return null;
            return animations[Random.Range(0, animations.Length)];
        }

        public void SetIdle()
        {
            currentState = AgentState.Idle;
            SetHighlight(false);
            StopGestureCoroutine();

            if (animator != null)
            {
                string anim = GetRandomAnimation(idleAnimations);
                if (!string.IsNullOrEmpty(anim))
                {
                    // Strongest method: Rebind and play
                    animator.Rebind();
                    animator.Play(anim, 0, 0f);
                    Debug.Log($"[{agentName}] Idle animation: {anim} (forced)");
                }
            }

            lipSyncController?.StopLipSync();
        }

        public void SetThinking()
        {
            currentState = AgentState.Thinking;
            SetHighlight(true, thinkingColor);
            StopGestureCoroutine();

            if (animator != null)
            {
                string anim = GetRandomAnimation(thinkingAnimations);
                if (!string.IsNullOrEmpty(anim))
                {
                    animator.CrossFade(anim, 0.1f);
                    Debug.Log($"[{agentName}] Thinking animation: {anim}");
                }
            }
        }

        public void SetSpeaking()
        {
            currentState = AgentState.Speaking;
            SetHighlight(true, speakingColor);

            if (animator != null)
            {
                string anim = GetRandomAnimation(speakingAnimations);
                if (!string.IsNullOrEmpty(anim))
                {
                    animator.CrossFade(anim, 0.1f);
                    Debug.Log($"[{agentName}] Speaking animation: {anim}");
                }

                // Optionally start gesture routine
                if (gestureAnimations.Length > 0 && gestureChance > 0)
                {
                    gestureCoroutine = StartCoroutine(GestureRoutine());
                }
            }
        }

        /// <summary>
        /// Periodically trigger random gestures while speaking
        /// </summary>
        private IEnumerator GestureRoutine()
        {
            while (currentState == AgentState.Speaking)
            {
                // Wait 3-6 seconds between gesture checks
                yield return new WaitForSeconds(Random.Range(3f, 6f));

                if (currentState != AgentState.Speaking)
                    break;

                // Random chance to play gesture
                if (Random.value < gestureChance)
                {
                    string gesture = GetRandomAnimation(gestureAnimations);
                    if (!string.IsNullOrEmpty(gesture))
                    {
                        animator.SetTrigger(gesture);
                        Debug.Log($"[{agentName}] Gesture: {gesture}");
                    }
                }
            }
        }

        private void StopGestureCoroutine()
        {
            if (gestureCoroutine != null)
            {
                StopCoroutine(gestureCoroutine);
                gestureCoroutine = null;
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

        public void PlayLipSync(VisemeEvent[] visemeData, AudioSource audioSource = null)
        {
            if (lipSyncController != null)
            {
                // Set audio source for precise sync
                lipSyncController.syncAudioSource = audioSource;
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

    // Note: VisemeBlendshapeMapping class is defined in LipSyncController.cs
}
