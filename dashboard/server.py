#!/usr/bin/env python3
"""
Hyper Video Studio - Multi-Project Command & Control Dashboard Server
Async aiohttp server with WebSockets, live media streaming, REST APIs,
multi-project workspace isolation, and real-time job execution tracking.
"""

import os
import sys
import json
import asyncio
import datetime
import subprocess
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

from core.config import load_config, save_config, ASPECT_RATIOS, THEMES, normalize_env_path
normalize_env_path()
from core.cron_manager import get_scheduler_status, install_scheduler, remove_scheduler
from core.project_manager import (
    list_projects,
    get_project,
    create_project,
    update_project,
    delete_project,
    get_project_dir
)

active_ws_clients = set()
running_task = None
current_job_logs = []

def broadcast_log(msg):
    current_job_logs.append(msg)
    if len(current_job_logs) > 500:
        current_job_logs.pop(0)
    for ws in list(active_ws_clients):
        try:
            asyncio.create_task(ws.send_str(msg))
        except Exception:
            pass

async def index_handler(request):
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return web.FileResponse(html_path)
    return web.Response(text="Dashboard UI not found", status=404)

# ----------------- Projects API Handlers -----------------

async def list_projects_api(request):
    projects = list_projects()
    return web.json_response({
        "status": "success",
        "projects": projects
    })

async def create_project_api(request):
    try:
        data = await request.json()
        new_proj = create_project(data)
        return web.json_response({"status": "success", "project": new_proj})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def get_project_api(request):
    pid = request.match_info.get("id")
    p = get_project(pid)
    if not p:
        return web.json_response({"error": "Project not found"}, status=404)
    return web.json_response({"status": "success", "project": p})

async def update_project_api(request):
    pid = request.match_info.get("id")
    try:
        data = await request.json()
        updated = update_project(pid, data)
        if not updated:
            return web.json_response({"error": "Project not found"}, status=404)
        return web.json_response({"status": "success", "project": updated})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def delete_project_api(request):
    pid = request.match_info.get("id")
    res = delete_project(pid)
    return web.json_response({"status": "success" if res else "failed"})

async def project_media_handler(request):
    pid = request.match_info.get("id")
    folder = request.match_info.get("folder")
    filename = request.match_info.get("filename")
    
    file_path = os.path.join(get_project_dir(pid), "output", folder, filename)
    if os.path.exists(file_path):
        return web.FileResponse(file_path)
    return web.Response(text="File not found", status=404)

# ----------------- General Studio API -----------------

async def status_handler(request):
    pid = request.query.get("project")
    sched = get_scheduler_status()
    cfg = load_config()
    
    latest_jobs = []
    active_project = None
    if pid:
        active_project = get_project(pid)
        if active_project:
            latest_jobs = active_project.get("jobs", [])
    
    if not latest_jobs and os.path.exists(OUTPUT_BASE_DIR):
        dirs = sorted([d for d in os.listdir(OUTPUT_BASE_DIR) if os.path.isdir(os.path.join(OUTPUT_BASE_DIR, d))], reverse=True)
        for d in dirs[:10]:
            man_path = os.path.join(OUTPUT_BASE_DIR, d, "manifest.json")
            if os.path.exists(man_path):
                try:
                    with open(man_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["folder_name"] = d
                        latest_jobs.append(data)
                except Exception:
                    pass

    return web.json_response({
        "is_running": (running_task is not None and not running_task.done()),
        "config": cfg,
        "active_project": active_project,
        "scheduler": sched,
        "aspect_ratios": ASPECT_RATIOS,
        "themes": THEMES,
        "latest_jobs": latest_jobs
    })

async def run_pipeline_worker(payload):
    global running_task
    current_job_logs.clear()
    cmd = [sys.executable, "-u", os.path.join(BASE_DIR, "cli.py"), "run-pipeline"]
    
    if payload.get("project_id"):
        cmd.extend(["--project", payload["project_id"]])
    if payload.get("topic"):
        cmd.extend(["--topic", payload["topic"]])
    if payload.get("hook"):
        cmd.extend(["--hook", payload["hook"]])
    if payload.get("aspect_ratio"):
        cmd.extend(["--aspect", payload["aspect_ratio"]])
    if payload.get("theme"):
        cmd.extend(["--theme", payload["theme"]])

    broadcast_log(f"🚀 Initializing Video Pipeline Engine: {' '.join(cmd)}\n")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=dict(os.environ)
    )

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace")
        broadcast_log(text)

    await proc.wait()
    broadcast_log(f"\n✨ Process exited with code {proc.returncode}\n")
    running_task = None

async def trigger_run_handler(request):
    global running_task
    if running_task is not None and not running_task.done():
        return web.json_response({"status": "already_running"}, status=400)

    try:
        data = await request.json()
    except Exception:
        data = {}

    running_task = asyncio.create_task(run_pipeline_worker(data))
    return web.json_response({"status": "started"})

async def stop_pipeline_handler(request):
    global running_task
    if running_task is not None and not running_task.done():
        running_task.cancel()
        running_task = None
        subprocess.run(["pkill", "-f", "render_frame_pipeline.js"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        broadcast_log("\n🛑 Video rendering cancelled by user.\n")
        return web.json_response({"status": "stopped"})
    return web.json_response({"status": "no_running_task"})

async def save_settings_handler(request):
    try:
        new_data = await request.json()
        pid = new_data.get("project_id")
        if pid:
            updated = update_project(pid, new_data)
            return web.json_response({"status": "saved", "project": updated})

        cfg = load_config()
        for k, v in new_data.items():
            if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
        save_config(cfg)
        return web.json_response({"status": "saved", "config": cfg})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def scheduler_manage_handler(request):
    try:
        data = await request.json()
        action = data.get("action")
        if action == "install":
            hour = int(data.get("hour", 10))
            minute = int(data.get("minute", 30))
            res = install_scheduler(hour, minute)
            return web.json_response({"status": "success", "result": res})
        elif action == "remove":
            res = remove_scheduler()
            return web.json_response({"status": "success", "result": res})
        elif action == "status":
            return web.json_response({"status": "success", "result": get_scheduler_status()})
        return web.json_response({"error": "Unknown action"}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def media_stream_handler(request):
    folder = request.match_info.get("folder")
    filename = request.match_info.get("filename")
    file_path = os.path.join(OUTPUT_BASE_DIR, folder, filename)
    
    if os.path.exists(file_path):
        return web.FileResponse(file_path)
    return web.Response(text="File not found", status=404)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    active_ws_clients.add(ws)

    for line in current_job_logs:
        await ws.send_str(line)

    try:
        async for msg in ws:
            pass
    finally:
        active_ws_clients.remove(ws)
    return ws

def create_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/status", status_handler)
    app.router.add_get("/api/projects", list_projects_api)
    app.router.add_post("/api/projects", create_project_api)
    app.router.add_get("/api/projects/{id}", get_project_api)
    app.router.add_post("/api/projects/{id}", update_project_api)
    app.router.add_delete("/api/projects/{id}", delete_project_api)
    app.router.add_get("/api/projects/{id}/media/{folder}/{filename}", project_media_handler)
    app.router.add_post("/api/run", trigger_run_handler)
    app.router.add_post("/api/stop", stop_pipeline_handler)
    app.router.add_post("/api/settings", save_settings_handler)
    app.router.add_post("/api/scheduler", scheduler_manage_handler)
    app.router.add_get("/api/media/{folder}/{filename}", media_stream_handler)
    app.router.add_get("/api/ws/logs", websocket_handler)
    app.router.add_static("/static", STATIC_DIR)
    return app

def start_server(host="0.0.0.0", port=8585):
    app = create_app()
    print(f"🌟 Hyper Video Studio Multi-Project Dashboard on http://{host}:{port}")
    web.run_app(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
