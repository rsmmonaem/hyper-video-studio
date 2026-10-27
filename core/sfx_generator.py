#!/usr/bin/env python3
"""
Procedural Studio Sound Effects (SFX) Synthesizer
Synthesizes broadcast-grade 44.1kHz 16-bit PCM WAV sound effects without external downloads:
- whoosh.wav : cinematic transition swoosh
- pop.wav    : tactile UI pop
- click.wav  : modern terminal / keyboard click
- riser.wav  : dramatic suspense buildup riser
- boom.wav   : deep sub-bass architectural impact
"""

import os
import math
import wave
import struct
import random

SAMPLE_RATE = 44100

def write_wav(file_path, samples):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with wave.open(file_path, "w") as wav_file:
        nchannels = 1
        sampwidth = 2
        framerate = SAMPLE_RATE
        nframes = len(samples)
        wav_file.setparams((nchannels, sampwidth, framerate, nframes, "NONE", "not compressed"))
        
        packed_frames = bytearray()
        for s in samples:
            val = max(-1.0, min(1.0, s))
            int_val = int(val * 32767.0)
            packed_frames.extend(struct.pack("<h", int_val))
        wav_file.writeframes(packed_frames)

def generate_whoosh(duration=0.45):
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(total_samples):
        t = i / total_samples
        # Bell envelope
        envelope = math.sin(t * math.pi) ** 2
        # Sweeping noise band
        center_freq = 300 + 1200 * math.sin(t * math.pi)
        white_noise = random.uniform(-1.0, 1.0)
        sine_mod = math.sin(2 * math.pi * center_freq * (i / SAMPLE_RATE))
        val = (white_noise * 0.4 + sine_mod * 0.6) * envelope * 0.75
        samples.append(val)
    return samples

def generate_pop(duration=0.12):
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        freq = 900 * math.exp(-25 * t)
        decay = math.exp(-35 * t)
        val = math.sin(2 * math.pi * freq * t) * decay * 0.8
        samples.append(val)
    return samples

def generate_click(duration=0.04):
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        decay = math.exp(-120 * t)
        val = (random.uniform(-0.5, 0.5) + math.sin(2 * math.pi * 1800 * t) * 0.5) * decay
        samples.append(val)
    return samples

def generate_boom(duration=0.9):
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        freq = 65 * math.exp(-3.5 * t)
        decay = math.exp(-4.2 * t)
        sub = math.sin(2 * math.pi * freq * t) * decay
        punch = math.sin(2 * math.pi * 120 * t) * math.exp(-28 * t) * 0.4
        samples.append((sub + punch) * 0.9)
    return samples

def generate_riser(duration=1.2):
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(total_samples):
        progress = i / total_samples
        t = i / SAMPLE_RATE
        freq = 120 + 750 * (progress ** 2.2)
        amp = progress ** 1.5
        val = (math.sin(2 * math.pi * freq * t) * 0.7 + random.uniform(-0.3, 0.3) * progress) * amp * 0.7
        samples.append(val)
    return samples

def ensure_all_sfx(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    registry = {
        "whoosh.wav": generate_whoosh(),
        "pop.wav": generate_pop(),
        "click.wav": generate_click(),
        "boom.wav": generate_boom(),
        "riser.wav": generate_riser()
    }
    for filename, samples in registry.items():
        target = os.path.join(output_dir, filename)
        if not os.path.exists(target):
            write_wav(target, samples)
            print(f"🎵 Synthesized SFX: {filename}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sfx_dir = os.path.join(os.path.dirname(current_dir), "assets", "sfx")
    ensure_all_sfx(sfx_dir)
