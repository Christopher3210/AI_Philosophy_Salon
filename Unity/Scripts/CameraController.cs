// CameraController.cs
// Smooth camera follow for the active speaker + mouse look during debate

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
        public float closeupHeight = 170f;
        [Tooltip("Where on the speaker to look at (Y offset from speaker position)")]
        public float lookAtHeightOffset = 50f;

        [Header("Smoothing")]
        public float moveSpeed = 2f;
        public float rotateSpeed = 2f;
        public float returnSpeed = 1.5f;

        [Header("Mouse Look")]
        [Tooltip("Enable mouse look during debate")]
        public bool mouseLookEnabled = true;
        [Tooltip("Mouse sensitivity")]
        public float mouseSensitivity = 2f;
        [Tooltip("Maximum horizontal rotation from base angle (degrees)")]
        public float maxYawOffset = 40f;
        [Tooltip("Maximum vertical rotation from base angle (degrees)")]
        public float maxPitchOffset = 25f;
        [Tooltip("Hold right mouse button to look around")]
        public bool requireRightClick = true;

        private Vector3 overviewPosition;
        private Quaternion overviewRotation;
        private Vector3 targetPosition;
        private Quaternion targetRotation;
        private Transform currentTarget;
        private bool isFollowing = false;

        // Mouse look state
        private float yawOffset = 0f;
        private float pitchOffset = 0f;
        private Quaternion baseRotation;
        private bool isMouseLooking = false;

        void Start()
        {
            overviewPosition = transform.position;
            overviewRotation = transform.rotation;
            targetPosition = overviewPosition;
            targetRotation = overviewRotation;
            baseRotation = overviewRotation;
        }

        void LateUpdate()
        {
            // Handle mouse look input
            HandleMouseLook();

            float speed = isFollowing ? moveSpeed : returnSpeed;
            transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * speed);

            if (isMouseLooking)
            {
                // Apply mouse look rotation on top of base rotation
                Quaternion yawRot = Quaternion.AngleAxis(yawOffset, Vector3.up);
                Quaternion pitchRot = Quaternion.AngleAxis(-pitchOffset, transform.right);
                Quaternion finalRotation = yawRot * baseRotation * Quaternion.Euler(-pitchOffset, 0, 0);

                // Reconstruct: apply yaw globally, pitch locally
                Vector3 baseEuler = baseRotation.eulerAngles;
                finalRotation = Quaternion.Euler(baseEuler.x + pitchOffset, baseEuler.y + yawOffset, 0);

                transform.rotation = Quaternion.Slerp(transform.rotation, finalRotation, Time.deltaTime * 10f);
            }
            else
            {
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * speed);
            }
        }

        private void HandleMouseLook()
        {
            if (!mouseLookEnabled) return;

            if (requireRightClick && Input.GetMouseButtonDown(1))
            {
                isMouseLooking = true;
                baseRotation = targetRotation;
                yawOffset = 0f;
                pitchOffset = 0f;
            }

            if (isMouseLooking && Input.GetMouseButton(1))
            {
                float mouseX = Input.GetAxis("Mouse X") * mouseSensitivity;
                float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;

                yawOffset = Mathf.Clamp(yawOffset + mouseX, -maxYawOffset, maxYawOffset);
                pitchOffset = Mathf.Clamp(pitchOffset - mouseY, -maxPitchOffset, maxPitchOffset);
            }

            if (isMouseLooking && Input.GetMouseButtonUp(1))
            {
                isMouseLooking = false;
                yawOffset = 0f;
                pitchOffset = 0f;
            }
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

            // Place camera in front of the speaker's face
            Vector3 facingDir = speaker.forward;
            facingDir.y = 0;
            facingDir.Normalize();

            targetPosition = speakerPos + facingDir * closeupDistance;
            targetPosition.y = closeupHeight;

            targetRotation = Quaternion.LookRotation(lookAtPoint - targetPosition);

            // Update base rotation for mouse look
            baseRotation = targetRotation;
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
            baseRotation = overviewRotation;

            // Reset mouse look
            if (isMouseLooking)
            {
                isMouseLooking = false;
                yawOffset = 0f;
                pitchOffset = 0f;
            }
        }

        public bool IsFollowing => isFollowing;
    }
}
