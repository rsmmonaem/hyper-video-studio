#!/usr/bin/env python3
"""
Hyper Video Studio - Multi-Project & Multi-Workspace Manager
Allows users to manage multiple independent video channels/projects,
each with their own aspect ratio, themes, voices, schedules, and outputs.
"""

import os
import re
import json
import shutil
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text) or "project"

def ensure_projects_dir():
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    if not os.listdir(PROJECTS_DIR):
        init_default_projects()

def init_default_projects():
    starters = [
        {
            "id": "ftltd-tech-reels",
            "name": "FTLTD Bengali Tech Reels",
            "description": "High-retention 60-second vertical tech reels in Bengali covering system design and software architecture.",
            "category": "Software Architecture",
            "aspect_ratio": "9:16",
            "theme": "cyber_cyan",
            "language": "bn",
            "voice": "bn-IN-BashkarNeural",
            "branding": {
                "author": "Rsm Monaem",
                "brand_name": "FTLTD",
                "brand_tagline": "Future TECH Limited",
                "cta_text": "ফলো ও সাবস্ক্রাইব করুন"
            },
            "cron": {
                "enabled": True,
                "hour": 10,
                "minute": 30
            }
        },
        {
            "id": "devops-cloud-masterclass",
            "name": "DevOps & Cloud Masterclass",
            "description": "Comprehensive 16:9 YouTube landscape breakdowns on Kubernetes, Docker, CI/CD, and Nginx high availability.",
            "category": "Cloud & DevOps",
            "aspect_ratio": "16:9",
            "theme": "fire_ember",
            "language": "bn",
            "voice": "bn-BD-PradeepNeural",
            "branding": {
                "author": "Rsm Monaem",
                "brand_name": "DevOps Pro",
                "brand_tagline": "Enterprise Cloud Systems",
                "cta_text": "চ্যানেলটি সাবস্ক্রাইব করুন"
            },
            "cron": {
                "enabled": False,
                "hour": 18,
                "minute": 0
            }
        },
        {
            "id": "ai-microservices-daily",
            "name": "AI & Microservices Daily",
            "description": "Square feed and shorts exploring Kafka event-driven pipelines, distributed systems, and modern AI automation.",
            "category": "Distributed Systems & AI",
            "aspect_ratio": "1:1",
            "theme": "matrix_terminal",
            "language": "en",
            "voice": "en-US-AndrewMultilingualNeural",
            "branding": {
                "author": "Rsm Monaem",
                "brand_name": "AI Systems",
                "brand_tagline": "Autonomous Tech Engineering",
                "cta_text": "Follow for daily insights"
            },
            "cron": {
                "enabled": False,
                "hour": 12,
                "minute": 0
            }
        }
    ]

    for p in starters:
        _save_new_project(p)

def _save_new_project(data):
    pid = data.get("id") or slugify(data.get("name", "project"))
    p_dir = os.path.join(PROJECTS_DIR, pid)
    os.makedirs(os.path.join(p_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(p_dir, "logs"), exist_ok=True)

    project_data = {
        "id": pid,
        "name": data.get("name", "New Project"),
        "description": data.get("description", "Autonomous developer video project"),
        "category": data.get("category", "Software Architecture"),
        "aspect_ratio": data.get("aspect_ratio", "9:16"),
        "theme": data.get("theme", "cyber_cyan"),
        "language": data.get("language", "bn"),
        "voice": data.get("voice", "bn-IN-BashkarNeural"),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "branding": data.get("branding", {
            "author": "Rsm Monaem",
            "brand_name": "FTLTD",
            "brand_tagline": "Future TECH Limited",
            "cta_text": "ফলো ও সাবস্ক্রাইব করুন"
        }),
        "cron": data.get("cron", {
            "enabled": True,
            "hour": 10,
            "minute": 30
        }),
        "llm": data.get("llm", {
            "provider": "template",
            "api_key": "",
            "model": "gemini-2.5-flash"
        }),
        "audio": data.get("audio", {
            "provider": "edge_tts",
            "edge_voice": data.get("voice", "bn-IN-BashkarNeural"),
            "elevenlabs_api_key": "",
            "elevenlabs_voice_id": "j5PhP1QJv2DvlhRv3mEv",
            "openai_api_key": "",
            "enable_sfx": True
        })
    }

    meta_file = os.path.join(p_dir, "project.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)

    return project_data

def create_project(data):
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    return _save_new_project(data)

def get_project_dir(project_id):
    return os.path.join(PROJECTS_DIR, project_id)

def list_projects():
    ensure_projects_dir()
    projects = []
    for pid in sorted(os.listdir(PROJECTS_DIR)):
        p_dir = os.path.join(PROJECTS_DIR, pid)
        meta_file = os.path.join(p_dir, "project.json")
        if os.path.isdir(p_dir) and os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Count videos in output
                out_dir = os.path.join(p_dir, "output")
                count = 0
                latest_thumb = None
                latest_video = None
                if os.path.exists(out_dir):
                    subdirs = sorted([d for d in os.listdir(out_dir) if os.path.isdir(os.path.join(out_dir, d))], reverse=True)
                    count = len(subdirs)
                    if subdirs:
                        top_d = subdirs[0]
                        top_path = os.path.join(out_dir, top_d)
                        man_file = os.path.join(top_path, "manifest.json")
                        if os.path.exists(man_file):
                            try:
                                with open(man_file, "r", encoding="utf-8") as mf:
                                    m_data = json.load(mf)
                                    latest_thumb = f"/api/projects/{pid}/media/{top_d}/thumbnail_16_9.jpg"
                                    latest_video = m_data.get("video")
                            except Exception:
                                pass
                        else:
                            # Fallback check
                            if os.path.exists(os.path.join(top_path, "thumbnail_16_9.jpg")):
                                latest_thumb = f"/api/projects/{pid}/media/{top_d}/thumbnail_16_9.jpg"
                
                data["video_count"] = count
                data["latest_thumbnail"] = latest_thumb
                data["latest_video"] = latest_video
                projects.append(data)
            except Exception as e:
                print(f"Error loading project {pid}: {e}")
    return projects

def get_project(project_id):
    p_dir = get_project_dir(project_id)
    meta_file = os.path.join(p_dir, "project.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Load output runs
        out_dir = os.path.join(p_dir, "output")
        jobs = []
        if os.path.exists(out_dir):
            for d in sorted(os.listdir(out_dir), reverse=True):
                d_path = os.path.join(out_dir, d)
                if not os.path.isdir(d_path):
                    continue
                man_path = os.path.join(d_path, "manifest.json")
                if os.path.exists(man_path):
                    try:
                        with open(man_path, "r", encoding="utf-8") as mf:
                            m_data = json.load(mf)
                            m_data["folder_name"] = d
                            jobs.append(m_data)
                    except Exception:
                        pass
                else:
                    # Resilient fallback: scan for produced media even if manifest was interrupted
                    files = os.listdir(d_path)
                    v_files = [f for f in files if f.endswith(".mp4")]
                    vid_final = next((f for f in v_files if not f.endswith("_raw.mp4")), None) or (v_files[0] if v_files else None)
                    t_16 = "thumbnail_16_9.jpg" if "thumbnail_16_9.jpg" in files else None
                    t_9 = "thumbnail_9_16.jpg" if "thumbnail_9_16.jpg" in files else None
                    aud = "master_audio.mp3" if "master_audio.mp3" in files else None

                    if vid_final or t_16 or t_9 or aud:
                        m_data = {
                            "folder_name": d,
                            "created_at": d.split("_")[0] if "_" in d else "Recent",
                            "topic": {
                                "topic": data.get("name", "Video Production"),
                                "hook": data.get("draft", {}).get("hook") or "Project Media Output",
                                "category": data.get("category", "Production")
                            },
                            "video": os.path.join(d_path, vid_final) if vid_final else None,
                            "thumbnails": {
                                "16_9": os.path.join(d_path, t_16) if t_16 else None,
                                "9_16": os.path.join(d_path, t_9) if t_9 else None
                            },
                            "audio": {
                                "path": os.path.join(d_path, aud) if aud else None
                            }
                        }
                        try:
                            with open(man_path, "w", encoding="utf-8") as mf:
                                json.dump(m_data, mf, indent=2, ensure_ascii=False)
                        except Exception:
                            pass
                        jobs.append(m_data)
        data["jobs"] = jobs
        return data
    return None

def create_project(data):
    ensure_projects_dir()
    name = (data.get("name") or "New Channel Project").strip()
    pid = data.get("id") or slugify(name)
    p_dir = get_project_dir(pid)

    # Ensure uniqueness
    counter = 1
    base_pid = pid
    while os.path.exists(p_dir):
        pid = f"{base_pid}-{counter}"
        p_dir = get_project_dir(pid)
        counter += 1

    os.makedirs(os.path.join(p_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(p_dir, "logs"), exist_ok=True)

    author = data.get("author") or data.get("branding", {}).get("author") or "Host"
    brand_name = data.get("brand_name") or data.get("branding", {}).get("brand_name") or name
    handle = data.get("handle") or data.get("branding", {}).get("handle") or f"@{slugify(name)}"
    category = data.get("category", "Software Architecture")

    project_data = {
        "id": pid,
        "name": name,
        "description": data.get("description", f"Autonomous video studio for {name}"),
        "category": category,
        "aspect_ratio": data.get("aspect_ratio", "9:16"),
        "theme": data.get("theme", "cyber_cyan"),
        "language": data.get("language", "bn"),
        "voice": data.get("voice", "bn-IN-BashkarNeural"),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "branding": {
            "author": author,
            "brand_name": brand_name,
            "handle": handle,
            "brand_tagline": data.get("branding", {}).get("brand_tagline", category),
            "cta_text": data.get("branding", {}).get("cta_text", "ফলো ও সাবস্ক্রাইব করুন")
        },
        "draft": data.get("draft", {
            "mode": "autonomous",
            "topic": "",
            "hook": "",
            "scene_1": "",
            "scene_2": "",
            "scene_3": "",
            "scene_4": ""
        }),
        "cron": data.get("cron", {
            "enabled": False,
            "hour": 10,
            "minute": 30
        }),
        "llm": data.get("llm", {
            "enabled": False,
            "provider": "template",
            "api_key": "",
            "model": "gemini-2.5-flash"
        }),
        "audio": data.get("audio", {
            "provider": "edge_tts",
            "edge_voice": data.get("voice", "bn-IN-BashkarNeural"),
            "elevenlabs_api_key": "",
            "elevenlabs_voice_id": "j5PhP1QJv2DvlhRv3mEv",
            "openai_api_key": "",
            "enable_sfx": True
        })
    }

    meta_file = os.path.join(p_dir, "project.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)

    return project_data

def update_project(project_id, updates):
    p_dir = get_project_dir(project_id)
    meta_file = os.path.join(p_dir, "project.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for k, v in updates.items():
            if isinstance(v, dict) and k in data and isinstance(data[k], dict):
                data[k].update(v)
            else:
                data[k] = v

        data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data
    return None

def delete_project(project_id):
    p_dir = get_project_dir(project_id)
    if os.path.exists(p_dir):
        shutil.rmtree(p_dir)
        return True
    return False
