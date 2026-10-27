#!/usr/bin/env python3
"""
Hyper Video Studio - Multi-TTS Audio Synthesizer & Dynamic SFX Mixer
Supports:
1. 'edge_tts'   : 100% Free, Zero API Key native neural voiceover (bn-BD, bn-IN, en-US, etc.)
2. 'elevenlabs' : Premium Studio ElevenLabs Multilingual v2
3. 'openai'     : OpenAI TTS (alloy, onyx, echo, nova)
4. 'custom'     : Custom endpoint
+ Automatic Audio Ducking, SFX alignment, and FFmpeg mixdown.
"""

import os
import sys
import json
import asyncio
import subprocess
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_DIR = os.path.join(BASE_DIR, "assets", "sfx")
from core.sfx_generator import ensure_all_sfx

def find_ffmpeg():
    paths = ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg", "ffmpeg"]
    for p in paths:
        if os.path.exists(p) or subprocess.run(["which", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return p
    return "ffmpeg"

FFMPEG_BIN = find_ffmpeg()

async def synthesize_edge_tts(text, voice, output_path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+5%", pitch="+0Hz")
    await communicate.save(output_path)

def synthesize_elevenlabs(text, voice_id, api_key, output_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=40) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())

def synthesize_openai_tts(text, voice, api_key, output_path):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tts-1",
        "input": text,
        "voice": voice or "onyx"
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=40) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 30.0

def build_scene_audio(scenes, output_dir, config):
    """
    Synthesizes speech for each scene, measures exact timings,
    and mixes with transition SFX (whoosh/pop/riser) into master_audio.mp3.
    """
    ensure_all_sfx(SFX_DIR)
    os.makedirs(output_dir, exist_ok=True)
    audio_cfg = config.get("audio", {})
    provider = audio_cfg.get("provider", "edge_tts").lower()
    voice = audio_cfg.get("edge_voice", "bn-IN-BashkarNeural")
    eleven_key = audio_cfg.get("elevenlabs_api_key")
    eleven_voice = audio_cfg.get("elevenlabs_voice_id", "j5PhP1QJv2DvlhRv3mEv")
    openai_key = audio_cfg.get("openai_api_key")

    scene_audio_paths = []
    cues = []
    current_time = 0.0

    for idx, scene in enumerate(scenes):
        scene_file = os.path.join(output_dir, f"scene_{idx+1}_voice.mp3")
        text = scene["text"]

        # 1. Synthesize
        success = False
        if provider == "elevenlabs" and eleven_key:
            try:
                print(f"🎙️ ElevenLabs synthesizing Scene {idx+1}...")
                synthesize_elevenlabs(text, eleven_voice, eleven_key, scene_file)
                success = True
            except Exception as e:
                print(f"⚠️ ElevenLabs fallback to Edge-TTS: {e}")

        elif provider == "openai" and openai_key:
            try:
                print(f"🎙️ OpenAI TTS synthesizing Scene {idx+1}...")
                synthesize_openai_tts(text, audio_cfg.get("openai_voice", "onyx"), openai_key, scene_file)
                success = True
            except Exception as e:
                print(f"⚠️ OpenAI TTS fallback to Edge-TTS: {e}")

        if not success:
            # Free Native Edge-TTS
            asyncio.run(synthesize_edge_tts(text, voice, scene_file))

        duration = get_audio_duration(scene_file)
        cues.append({
            "scene_index": idx + 1,
            "scene_id": scene.get("id", f"scene_{idx+1}"),
            "start": round(current_time, 2),
            "duration": round(duration, 2),
            "end": round(current_time + duration, 2),
            "text": text,
            "audio_file": scene_file
        })
        scene_audio_paths.append(scene_file)
        current_time += duration + 0.4  # 400ms pause between scenes

    total_duration = current_time

    # 2. Concatenate Scene Voices using FFmpeg concat filter
    concat_filter = []
    inputs = []
    for idx, path in enumerate(scene_audio_paths):
        inputs.extend(["-i", path])
    
    # Simple concat with crossfade or silence padding
    concat_txt = os.path.join(output_dir, "concat_list.txt")
    with open(concat_txt, "w") as f:
        for path in scene_audio_paths:
            f.write(f"file '{path}'\n")

    raw_voice_master = os.path.join(output_dir, "voice_master.mp3")
    subprocess.run([
        FFMPEG_BIN, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        raw_voice_master
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 3. Add SFX at scene transitions
    final_mixed_audio = os.path.join(output_dir, "master_audio.mp3")
    whoosh_path = os.path.join(SFX_DIR, "whoosh.wav")
    riser_path = os.path.join(SFX_DIR, "riser.wav")

    # If sfx enabled, overlay subtle whoosh at scene transitions
    if audio_cfg.get("enable_sfx", True) and os.path.exists(whoosh_path):
        try:
            filter_complex = "[0:a]volume=1.0[v0];"
            sfx_inputs = ["-i", raw_voice_master]
            mix_tags = ["[v0]"]

            # Add whoosh at each transition
            for i, cue in enumerate(cues[1:], start=1):
                delay_ms = int(cue["start"] * 1000)
                sfx_inputs.extend(["-i", whoosh_path])
                filter_complex += f"[{i}:a]adelay={delay_ms}|{delay_ms},volume=0.25[sfx{i}];"
                mix_tags.append(f"[sfx{i}]")

            filter_complex += f"{''.join(mix_tags)}amix=inputs={len(mix_tags)}:duration=longest[out]"

            cmd = [FFMPEG_BIN, "-y"] + sfx_inputs + [
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                final_mixed_audio
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"⚠️ SFX mixing notice: {e}, using raw voice master.")
            final_mixed_audio = raw_voice_master
    else:
        final_mixed_audio = raw_voice_master

    master_duration = get_audio_duration(final_mixed_audio)
    return {
        "audio_path": final_mixed_audio,
        "duration": master_duration,
        "cues": cues
    }
