using System;
using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.Data
{
    [Serializable]
    public class CutsceneSlide
    {
        public Sprite Illustration;
        [TextArea(3, 8)]
        public string NarrativeText;
        public string SpeakerName = "Prince Mandrew";
    }

    [CreateAssetMenu(fileName = "NewCutsceneData", menuName = "GBH England/Data/Cutscene Data")]
    public class CutsceneData : ScriptableObject
    {
        public string CutsceneID;
        public string Title = "The Royal Arena Champion";
        public List<CutsceneSlide> Slides = new List<CutsceneSlide>();
    }
}
