// CameraController.cs
// Smooth camera follow for the active speaker

using UnityEngine;

namespace PhilosophySalon
{
    public class CameraController : MonoBehaviour
    {
        [Header("References")]
        public DialogueManager dialogueManager;

        [Header("Close-up Settings")]
        [Tooltip("How far in front of the speaker the camera stops")]
        public float closeupDistance = 180f;
        [Tooltip("Camera height when zoomed in")]
        public float closeupHeight = 140f;
        [Tooltip("Where on the speaker to look at (Y offset from speaker position)")]
        public float lookAtHeightOffset = 50f;

        [Header("Smoothing")]
        public float moveSpeed = 2f;
        public float rotateSpeed = 2f;
        public float returnSpeed = 1.5f;

        private Vector3 overviewPosition;
        private Quaternion overviewRotation;
        private Vector3 targetPosition;
        private Quaternion targetRotation;
        private Transform currentTarget;
        private bool isFollowing = false;

        void Start()
        {
            // Store the initial camera position as the overview shot
            overviewPosition = transform.position;
            overviewRotation = transform.rotation;
            targetPosition = overviewPosition;
            targetRotation = overviewRotation;
        }

        void LateUpdate()
        {
            float speed = isFollowing ? moveSpeed : returnSpeed;
            transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * speed);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * speed);
        }

        /// <summary>
        /// Move camera to focus on a speaker, positioned in front of their face
        /// </summary>
        public void FocusOnSpeaker(Transform speaker)
        {
            if (speaker == null) return;

            currentTarget = speaker;
            isFollowing = true;

            Vector3 speakerPos = speaker.position;
            Vector3 lookAtPoint = speakerPos + Vector3.up * lookAtHeightOffset;

            // Place camera on the audience side (toward overview position)
            // This guarantees the camera stays inside the building
            Vector3 toAudience = (overviewPosition - speakerPos);
            toAudience.y = 0;
            toAudience.Normalize();

            targetPosition = speakerPos + toAudience * closeupDistance;
            targetPosition.y = closeupHeight;

            // Look at the speaker's upper body
            targetRotation = Quaternion.LookRotation(lookAtPoint - targetPosition);
        }

        /// <summary>
        /// Return camera to overview position
        /// </summary>
        public void ReturnToOverview()
        {
            currentTarget = null;
            isFollowing = false;
            targetPosition = overviewPosition;
            targetRotation = overviewRotation;
        }

        /// <summary>
        /// Check if camera is currently following a speaker
        /// </summary>
        public bool IsFollowing => isFollowing;
    }
}
