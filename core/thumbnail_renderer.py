#!/usr/bin/env python3
"""
Hyper Video Studio - High CTR Broadcast Thumbnail Generator
Renders ultra-sharp 1920x1080 (YouTube) and 1080x1920 (Reels cover) thumbnails
via Headless Chromium with glow effects, bold typography, and 3D badges.
"""

import os
import sys
import subprocess
from core.template_engine import render_template
from core.config import ASPECT_RATIOS, THEMES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "master_thumbnail.html")
RENDER_SCRIPT = os.path.join(BASE_DIR, "skills", "hyper-motion-engine", "render_frame_pipeline.js")

def generate_thumbnail(topic_data, output_path, aspect_ratio="16:9", theme_key="cyber_cyan", branding=None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    aspect_info = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
    width = aspect_info["width"]
    height = aspect_info["height"]
    theme = THEMES.get(theme_key, THEMES["cyber_cyan"])

    if branding is None:
        branding = {
            "author": "Rsm Monaem",
            "brand_name": "FTLTD",
            "cta_text": "WATCH NOW"
        }

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_raw = f.read()

    context = {
        "width": width,
        "height": height,
        "theme": theme,
        "topic": topic_data,
        "branding": branding
    }

    compiled_html = render_template(template_raw, context)
    temp_html_path = output_path + ".html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)

    # Launch node renderer
    cmd = [
        "node", RENDER_SCRIPT,
        "thumbnail",
        temp_html_path,
        output_path,
        str(width),
        str(height)
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"🎨 High-CTR Thumbnail Generated: {output_path}")
        return output_path
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
