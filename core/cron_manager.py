#!/usr/bin/env python3
"""
Hyper Video Studio - Zero-Terminal Cron & Autonomous Scheduler Manager
Allows full management of daily recurring runs directly from the web dashboard:
- macOS LaunchAgent (.plist)
- Linux / VPS user Crontab
- Built-in background timer fallback
"""

import os
import sys
import json
import shutil
import platform
import datetime
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHD_PLIST_NAME = "com.hypervideostudio.daily.plist"
USER_LAUNCHAGENTS_DIR = os.path.expanduser("~/Library/LaunchAgents")
PLIST_PATH = os.path.join(USER_LAUNCHAGENTS_DIR, LAUNCHD_PLIST_NAME)
LOG_PATH = os.path.join(BASE_DIR, "logs", "scheduler.log")

def get_python_bin():
    return sys.executable or "/usr/bin/env python3"

def get_scheduler_status():
    is_mac = (platform.system() == "Darwin")
    installed = False
    schedule_time = "10:30 AM"
    scheduler_type = "launchd" if is_mac else "crontab"

    if is_mac and os.path.exists(PLIST_PATH):
        installed = True
        try:
            with open(PLIST_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                # Parse hour and minute
                import re
                h_match = re.search(r"<key>Hour</key>\s*<integer>(\d+)</integer>", content)
                m_match = re.search(r"<key>Minute</key>\s*<integer>(\d+)</integer>", content)
                if h_match and m_match:
                    h = int(h_match.group(1))
                    m = int(m_match.group(1))
                    schedule_time = f"{h:02d}:{m:02d}"
        except Exception:
            pass
    elif not is_mac:
        # Check crontab -l
        try:
            res = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "hyper-video-studio" in res.stdout:
                installed = True
                for line in res.stdout.splitlines():
                    if "hyper-video-studio" in line and not line.strip().startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            schedule_time = f"{int(parts[1]):02d}:{int(parts[0]):02d}"
                        break
        except Exception:
            pass

    return {
        "platform": platform.system(),
        "scheduler_type": scheduler_type,
        "is_active": installed,
        "schedule_time": schedule_time,
        "last_log": get_last_scheduler_log()
    }

def get_last_scheduler_log():
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return "".join(lines[-20:])
        except Exception:
            pass
    return "No scheduler executions recorded yet."

def install_scheduler(hour=10, minute=30):
    is_mac = (platform.system() == "Darwin")
    runner_script = os.path.join(BASE_DIR, "cli.py")
    python_bin = get_python_bin()

    if is_mac:
        os.makedirs(USER_LAUNCHAGENTS_DIR, exist_ok=True)
        # Unload previous if loaded
        if os.path.exists(PLIST_PATH):
            subprocess.run(["launchctl", "unload", PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hypervideostudio.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>{runner_script}</string>
        <string>run-pipeline</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{int(hour)}</integer>
        <key>Minute</key>
        <integer>{int(minute)}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>{LOG_PATH}</string>
</dict>
</plist>
"""
        with open(PLIST_PATH, "w", encoding="utf-8") as f:
            f.write(plist_content)

        subprocess.run(["launchctl", "load", PLIST_PATH], check=True)
        return {"status": "installed", "type": "launchd", "time": f"{hour:02d}:{minute:02d}"}

    else:
        # Linux / VPS crontab
        cron_line = f"{int(minute)} {int(hour)} * * * {python_bin} {runner_script} run-pipeline >> {LOG_PATH} 2>&1 # hyper-video-studio"
        
        # Read existing crontab
        res = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        existing = [line for line in res.stdout.splitlines() if "hyper-video-studio" not in line]
        existing.append(cron_line)
        new_crontab = "\n".join(existing) + "\n"

        p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        p.communicate(new_crontab)
        return {"status": "installed", "type": "crontab", "time": f"{hour:02d}:{minute:02d}"}

def remove_scheduler():
    is_mac = (platform.system() == "Darwin")
    if is_mac and os.path.exists(PLIST_PATH):
        subprocess.run(["launchctl", "unload", PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(PLIST_PATH)
        return {"status": "removed", "type": "launchd"}
    elif not is_mac:
        res = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        existing = [line for line in res.stdout.splitlines() if "hyper-video-studio" not in line]
        new_crontab = "\n".join(existing) + "\n"
        p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        p.communicate(new_crontab)
        return {"status": "removed", "type": "crontab"}
    return {"status": "not_active"}
