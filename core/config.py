#!/usr/bin/env python3
"""
Hyper Video Studio - Global Configuration & Settings Manager
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

ASPECT_RATIOS = {
    "9:16": {"width": 1080, "height": 1920, "name": "Vertical Reels/Shorts/TikTok (1080x1920)"},
    "16:9": {"width": 1920, "height": 1080, "name": "Horizontal YouTube/Desktop (1920x1080)"},
    "1:1":  {"width": 1080, "height": 1080, "name": "Square Feed (1080x1080)"},
    "4:5":  {"width": 1080, "height": 1350, "name": "Instagram Portrait Feed (1080x1350)"},
    "4:3":  {"width": 1440, "height": 1080, "name": "Classic Presentation (1440x1080)"},
    "3:4":  {"width": 1080, "height": 1440, "name": "Tall Social Feed (1080x1440)"}
}

THEMES = {
    "cyber_cyan": {
        "name": "Cyber Cyan (Dark Obsidian & Neon Blue)",
        "bg_gradient": "linear-gradient(175deg, #070d19 0%, #0d1b2a 45%, #050a14 100%)",
        "primary": "#00d4ff",
        "secondary": "#38bdf8",
        "accent": "#0ea5e9",
        "glow": "rgba(0, 212, 255, 0.4)",
        "card_bg": "rgba(13, 27, 42, 0.82)",
        "border": "rgba(0, 212, 255, 0.28)",
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8"
    },
    "fire_ember": {
        "name": "Fire Ember (Obsidian Charcoal & Radiant Orange)",
        "bg_gradient": "linear-gradient(175deg, #180b06 0%, #2a1107 45%, #120703 100%)",
        "primary": "#ff6600",
        "secondary": "#ff9900",
        "accent": "#f97316",
        "glow": "rgba(255, 102, 0, 0.4)",
        "card_bg": "rgba(35, 16, 8, 0.85)",
        "border": "rgba(255, 102, 0, 0.32)",
        "text_primary": "#ffffff",
        "text_secondary": "#fdba74"
    },
    "matrix_terminal": {
        "name": "Matrix Terminal (Deep Hacker Green & Glass)",
        "bg_gradient": "linear-gradient(175deg, #04130a 0%, #062312 45%, #020b06 100%)",
        "primary": "#10b981",
        "secondary": "#34d399",
        "accent": "#059669",
        "glow": "rgba(16, 185, 129, 0.4)",
        "card_bg": "rgba(6, 35, 18, 0.85)",
        "border": "rgba(16, 185, 129, 0.3)",
        "text_primary": "#ecfdf5",
        "text_secondary": "#a7f3d0"
    },
    "tokyo_neon": {
        "name": "Tokyo Midnight (Royal Purple & Magenta Glow)",
        "bg_gradient": "linear-gradient(175deg, #120724 0%, #210d3e 45%, #0a0414 100%)",
        "primary": "#c084fc",
        "secondary": "#e879f9",
        "accent": "#9333ea",
        "glow": "rgba(192, 132, 252, 0.42)",
        "card_bg": "rgba(28, 12, 53, 0.85)",
        "border": "rgba(192, 132, 252, 0.3)",
        "text_primary": "#faf5ff",
        "text_secondary": "#e9d5ff"
    },
    "clean_minimal": {
        "name": "Studio Obsidian (Neutral Monochrome & Titanium)",
        "bg_gradient": "linear-gradient(175deg, #090a0f 0%, #13151f 45%, #07080b 100%)",
        "primary": "#e2e8f0",
        "secondary": "#94a3b8",
        "accent": "#38bdf8",
        "glow": "rgba(226, 232, 240, 0.25)",
        "card_bg": "rgba(20, 22, 33, 0.85)",
        "border": "rgba(255, 255, 255, 0.16)",
        "text_primary": "#ffffff",
        "text_secondary": "#cbd5e1"
    }
}

DEFAULT_CONFIG = {
    "version": "1.0.0",
    "project_name": "Hyper Video Studio",
    "language": "bn",
    "default_aspect_ratio": "9:16",
    "default_theme": "cyber_cyan",
    "branding": {
        "author": "Rsm Monaem",
        "brand_name": "FTLTD",
        "brand_tagline": "Future TECH Limited",
        "cta_text": "ফলো ও সাবস্ক্রাইব করুন"
    },
    "llm": {
        "provider": "template",  # Options: 'template', 'gemini', 'openai', 'openrouter', 'custom'
        "api_key": "",
        "base_url": "",
        "model": "gemini-2.5-flash",
        "temperature": 0.7
    },
    "audio": {
        "provider": "edge_tts",  # Options: 'edge_tts', 'elevenlabs', 'openai', 'custom'
        "edge_voice": "bn-IN-BashkarNeural",  # bn-BD-PradeepNeural, bn-BD-NabanitaNeural, en-US-AndrewMultilingualNeural
        "elevenlabs_api_key": "",
        "elevenlabs_voice_id": "j5PhP1QJv2DvlhRv3mEv",
        "openai_api_key": "",
        "openai_voice": "onyx",
        "custom_tts_url": "",
        "ducking_volume": -22,
        "enable_sfx": True
    },
    "cron": {
        "enabled": True,
        "hour": 10,
        "minute": 30,
        "type": "launchd_or_cron"  # Auto detects launchd on macOS, crontab on Linux/VPS
    },
    "video_engine": {
        "fps": 24,
        "chromium_path": "",
        "ffmpeg_path": ""
    }
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge defaults for any missing keys
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        return merged
    except Exception as e:
        print(f"⚠️ Error reading config.json, returning defaults: {e}")
        return DEFAULT_CONFIG

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg
