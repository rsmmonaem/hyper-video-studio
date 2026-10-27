---
name: audio-synthesizer
description: Multi-engine neural audio synthesis (Edge-TTS, ElevenLabs, OpenAI) with automatic cue timing and transition SFX mixdown.
---

# Audio Synthesizer Skill

Handles high-fidelity voiceover synthesis and dynamic audio mixing.

## Voiceover Providers
1. **Native Edge-TTS (100% Free / Zero API Key)**:
   - Bengali Voices: `bn-IN-BashkarNeural` (Energetic Male), `bn-BD-PradeepNeural` (BD Male), `bn-BD-NabanitaNeural` (BD Female).
   - Global English: `en-US-AndrewMultilingualNeural`.
2. **ElevenLabs Multilingual v2**:
   - High-fidelity studio voiceover using custom Voice IDs.
3. **OpenAI TTS**:
   - `onyx`, `alloy`, `nova` voices.

## Procedural SFX & Ducking
- Scene switches receive a subtle `whoosh.wav` transition sound effect.
- Key dilemmas and impacts receive low-frequency `boom.wav` and `riser.wav`.
- Master voiceover is prioritized with automatic audio ducking.
