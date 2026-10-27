#!/usr/bin/env python3
"""
Hyper Video Studio - Deterministic Motion Video Renderer
Compiles the GSAP-driven responsive HTML motion template, executes frame-by-frame
Chromium capture, and multiplexes studio audio into final broadcast MP4.
"""

import os
import sys
import json
import subprocess
from core.template_engine import render_template
from core.config import ASPECT_RATIOS, THEMES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "master_motion.html")
RENDER_SCRIPT = os.path.join(BASE_DIR, "skills", "hyper-motion-engine", "render_frame_pipeline.js")

def find_ffmpeg():
    paths = ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg", "ffmpeg"]
    for p in paths:
        if os.path.exists(p) or subprocess.run(["which", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return p
    return "ffmpeg"

FFMPEG_BIN = find_ffmpeg()

def render_motion_video(topic_data, audio_meta, output_mp4, aspect_ratio="9:16", theme_key="cyber_cyan", branding=None, fps=24):
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)
    
    aspect_info = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["9:16"])
    width = aspect_info["width"]
    height = aspect_info["height"]
    theme = THEMES.get(theme_key, THEMES["cyber_cyan"])

    if branding is None:
        branding = {
            "author": "Rsm Monaem",
            "brand_name": "FTLTD",
            "brand_tagline": "Future TECH Limited",
            "cta_text": "ফলো ও সাবস্ক্রাইব করুন"
        }

    total_duration = audio_meta["duration"]
    cues = audio_meta["cues"]
    master_audio_path = audio_meta["audio_path"]

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_raw = f.read()

    context = {
        "width": width,
        "height": height,
        "theme": theme,
        "topic": topic_data,
        "branding": branding,
        "total_duration": total_duration,
        "cues_json": json.dumps(cues)
    }

    compiled_html = render_template(template_raw, context)
    temp_html_path = output_mp4 + ".motion.html"
    raw_video_path = output_mp4.replace(".mp4", "_raw.mp4")

    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)

    try:
        # Step 1: Render video frames
        cmd_render = [
            "node", RENDER_SCRIPT,
            "video",
            temp_html_path,
            raw_video_path,
            str(width),
            str(height),
            str(total_duration),
            str(fps)
        ]
        subprocess.run(cmd_render, check=True)

        # Step 2: Mux audio + video with FFmpeg
        print(f"🎛️ Multiplexing master audio into video...")
        cmd_mux = [
            FFMPEG_BIN, "-y",
            "-i", raw_video_path,
            "-i", master_audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4
        ]
        subprocess.run(cmd_mux, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"🎬 Video rendering 100% complete: {output_mp4}")
        return output_mp4
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if os.path.exists(raw_video_path):
            os.remove(raw_video_path)
