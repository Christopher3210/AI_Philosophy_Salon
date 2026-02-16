// TeethSyncController.cs
// Mirrors blendshape weights from Head_Mesh to Teeth_Mesh each frame
// Attach to the character root (same level as AgentController)

using System.Collections.Generic;
using UnityEngine;

namespace PhilosophySalon
{
    public class TeethSyncController : MonoBehaviour
    {
        [Tooltip("The head SkinnedMeshRenderer (source of blendshape weights)")]
        public SkinnedMeshRenderer headRenderer;

        [Tooltip("The teeth SkinnedMeshRenderer (target to mirror weights to)")]
        public SkinnedMeshRenderer teethRenderer;

        // Cached mapping: headBlendshapeIndex -> teethBlendshapeIndex
        private int[] indexMap;
        private int headBlendCount;
        private bool initialized = false;

        void Start()
        {
            BuildIndexMap();
        }

        void BuildIndexMap()
        {
            if (headRenderer == null || headRenderer.sharedMesh == null ||
                teethRenderer == null || teethRenderer.sharedMesh == null)
            {
                Debug.LogWarning($"[TeethSync] {gameObject.name}: Missing head or teeth renderer");
                return;
            }

            Mesh headMesh = headRenderer.sharedMesh;
            Mesh teethMesh = teethRenderer.sharedMesh;
            headBlendCount = headMesh.blendShapeCount;

            // Build name->index lookup for teeth mesh
            var teethNameToIndex = new Dictionary<string, int>();
            for (int i = 0; i < teethMesh.blendShapeCount; i++)
            {
                teethNameToIndex[teethMesh.GetBlendShapeName(i)] = i;
            }

            // Map each head blendshape to the matching teeth blendshape by name
            indexMap = new int[headBlendCount];
            int matched = 0;
            for (int i = 0; i < headBlendCount; i++)
            {
                string name = headMesh.GetBlendShapeName(i);
                if (teethNameToIndex.TryGetValue(name, out int teethIndex))
                {
                    indexMap[i] = teethIndex;
                    matched++;
                }
                else
                {
                    indexMap[i] = -1; // No matching blendshape in teeth mesh
                }
            }

            initialized = true;
            Debug.Log($"[TeethSync] {gameObject.name}: Mapped {matched}/{headBlendCount} blendshapes from head to teeth");
        }

        void LateUpdate()
        {
            if (!initialized) return;

            for (int i = 0; i < headBlendCount; i++)
            {
                int teethIndex = indexMap[i];
                if (teethIndex >= 0)
                {
                    float weight = headRenderer.GetBlendShapeWeight(i);
                    teethRenderer.SetBlendShapeWeight(teethIndex, weight);
                }
            }
        }
    }
}
