#!/usr/bin/env python3
"""
Hyper Video Studio - Master Autonomous Pipeline & Batch Engine
Coordinates:
1. Topic synthesis & viral hook generation
2. Multi-provider audio synthesis & SFX mixdown
3. High-CTR thumbnail rendering
4. Deterministic GSAP motion video compilation (Multi-Aspect Ratio)
5. Multi-platform copy formatting & manifest generation
"""

import os
import sys
import json
import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

from core.config import load_config, ASPECT_RATIOS
from core.project_manager import get_project, get_project_dir
from core.llm_engine import plan_content
from core.audio_engine import build_scene_audio
from core.thumbnail_renderer import generate_thumbnail
from core.video_renderer import render_motion_video

def format_social_copies(topic_data, branding):
    hook = topic_data.get("hook", "")
    topic = topic_data.get("topic", "")
    summary = topic_data.get("summary", "")
    tags = " ".join([f"#{t.replace(' ', '')}" for t in topic_data.get("core_tech", [])])

    return {
        "youtube": {
            "title": f"{hook} | {topic} #Shorts",
            "description": f"{summary}\n\n📌 আলোচনা: {topic}\n🏷️ ট্যাগ: {tags} #Coding #DevOps #SystemDesign #BanglaTech\n\nচ্যানেল সাবস্ক্রাইব করুন: {branding.get('brand_name')}",
            "tags": topic_data.get("core_tech", []) + ["System Design", "Bangla Tech", "Software Engineering"]
        },
        "facebook": {
            "text": f"🔥 {hook}\n\n{summary}\n\nসফটওয়্যার আর্কিটেকচার ও প্রোডাকশন স্কেলিং সম্পর্কিত নিয়মিত ইনসাইট পেতে পেজটিতে লাইক ও ফলো দিয়ে রাখুন!\n\n{tags} #FTLTD #DevOps"
        },
        "linkedin": {
            "text": f"💡 Engineering Architecture Case Study: {topic}\n\n{hook}\n\n{summary}\n\nKey Takeaways:\n1. Zero single point of failure.\n2. Isolate concurrency bottlenecks before scaling.\n\nWhat is your preferred approach in production? Share in comments!\n\n{tags} #SystemDesign #SoftwareEngineering"
        },
        "instagram": {
            "caption": f"⚡ {hook}\n\nSwipe to breakdown the architecture 👉\n\n{summary}\n\nFollow @{branding.get('brand_name').lower()} for daily developer insights!\n\n{tags} #programmer #devlife"
        }
    }

def run_pipeline(user_topic=None, user_hook=None, custom_scenes=None, aspect_ratio=None, theme=None, custom_dir=None, project_id=None):
    cfg = load_config()
    
    # If project_id provided, merge project-specific config
    project_meta = None
    if project_id:
        project_meta = get_project(project_id)
        if project_meta:
            cfg.update(project_meta)
            print(f"📁 Scoped Execution to Project: [{project_meta.get('name')}] ({project_id})")

    branding = cfg.get("branding", {})
    selected_aspect = aspect_ratio or cfg.get("aspect_ratio") or cfg.get("default_aspect_ratio", "9:16")
    selected_theme = theme or cfg.get("theme") or cfg.get("default_theme", "cyber_cyan")

    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")

    # Output directory
    if custom_dir:
        job_dir = custom_dir
    elif project_id:
        job_dir = os.path.join(get_project_dir(project_id), "output", f"{today_str}_{timestamp_str}")
    else:
        job_dir = os.path.join(OUTPUT_BASE_DIR, f"{today_str}_{timestamp_str}")
    os.makedirs(job_dir, exist_ok=True)

    print(f"🚀 Initializing Video Pipeline in: {job_dir}")
    print(f"📐 Target Aspect Ratio: {selected_aspect} ({ASPECT_RATIOS.get(selected_aspect, {}).get('name')})")
    print(f"🎨 Theme: {selected_theme}")

    # 1. Step 1: Content Planning
    print("📝 [1/5] Planning Content & Scene Structuring...")
    topic_data = plan_content(cfg, user_topic=user_topic, user_hook=user_hook)

    # If custom scenes are provided
    if custom_scenes and isinstance(custom_scenes, list) and len(custom_scenes) >= 2:
        scenes = custom_scenes
    else:
        scenes = [
            {"id": "scene_1", "text": topic_data["scene_1_hook"]},
            {"id": "scene_2", "text": topic_data["scene_2_problem"]},
            {"id": "scene_3", "text": topic_data["scene_3_solution"]},
            {"id": "scene_4", "text": topic_data["scene_4_outro"]}
        ]

    # 2. Step 2: Audio Synthesis & SFX Mixing
    print("🎙️ [2/5] Synthesizing Studio Audio with Scene Cues & SFX...")
    audio_meta = build_scene_audio(scenes, job_dir, cfg)
    print(f"✅ Master audio ready ({audio_meta['duration']:.1f}s): {audio_meta['audio_path']}")

    # 3. Step 3: High-CTR Thumbnail Studio
    print("🎨 [3/5] Generating Broadcast-Grade Thumbnails (16:9 and 9:16)...")
    thumb_16_9 = os.path.join(job_dir, "thumbnail_16_9.jpg")
    thumb_9_16 = os.path.join(job_dir, "thumbnail_9_16.jpg")
    
    generate_thumbnail(topic_data, thumb_16_9, aspect_ratio="16:9", theme_key=selected_theme, branding=branding)
    generate_thumbnail(topic_data, thumb_9_16, aspect_ratio="9:16", theme_key=selected_theme, branding=branding)

    # 4. Step 4: Motion Video Compilation
    print(f"🎬 [4/5] Rendering Deterministic Motion Graphics Video ({selected_aspect})...")
    final_video_path = os.path.join(job_dir, f"video_{selected_aspect.replace(':', '_')}.mp4")
    render_motion_video(
        topic_data=topic_data,
        audio_meta=audio_meta,
        output_mp4=final_video_path,
        aspect_ratio=selected_aspect,
        theme_key=selected_theme,
        branding=branding,
        fps=cfg.get("video_engine", {}).get("fps", 24)
    )

    # 5. Step 5: Multi-Platform Post Formatting & Manifest
    print("📋 [5/5] Formatting High-Converting Platform Posts & Manifest...")
    copies = format_social_copies(topic_data, branding)
    copies_file = os.path.join(job_dir, "social_media_posts.json")
    with open(copies_file, "w", encoding="utf-8") as f:
        json.dump(copies, f, indent=2, ensure_ascii=False)

    manifest = {
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "project_id": project_id,
        "aspect_ratio": selected_aspect,
        "theme": selected_theme,
        "topic": topic_data,
        "audio": {
            "duration": audio_meta["duration"],
            "cues": audio_meta["cues"],
            "path": audio_meta["audio_path"]
        },
        "thumbnails": {
            "16_9": thumb_16_9,
            "9_16": thumb_9_16
        },
        "video": final_video_path,
        "copies": copies
    }

    manifest_path = os.path.join(job_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✨ Production Run Completed Successfully in: {job_dir}")
    return manifest

def run_batch_pipeline(batch_items, aspect_ratio="9:16", theme="cyber_cyan"):
    """
    Executes a batch of multiple videos sequentially.
    batch_items: list of dicts with keys: topic, hook, scenes (optional)
    """
    results = []
    print(f"📦 Starting Batch Production for {len(batch_items)} videos...")
    for idx, item in enumerate(batch_items, 1):
        print(f"\n==========================================")
        print(f"🎬 Processing Batch Video [{idx}/{len(batch_items)}]: {item.get('topic')}")
        print(f"==========================================")
        try:
            res = run_pipeline(
                user_topic=item.get("topic"),
                user_hook=item.get("hook"),
                custom_scenes=item.get("scenes"),
                aspect_ratio=item.get("aspect_ratio", aspect_ratio),
                theme=item.get("theme", theme)
            )
            results.append({"status": "success", "topic": item.get("topic"), "manifest": res})
        except Exception as e:
            traceback.print_exc()
            results.append({"status": "failed", "topic": item.get("topic"), "error": str(e)})

    return results
