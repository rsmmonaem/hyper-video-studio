#!/usr/bin/env python3
"""
Hyper Video Studio - Command Line Interface (CLI)
Usage:
  ./cli.py run-pipeline [--topic "..." --hook "..."] [--aspect 9:16|16:9|1:1] [--theme cyber_cyan|fire_ember]
  ./cli.py dashboard [--host 0.0.0.0] [--port 8585]
  ./cli.py scheduler [--status] [--install --hour 10 --minute 30] [--remove]
"""

import sys
import argparse
from core.pipeline import run_pipeline
from core.cron_manager import get_scheduler_status, install_scheduler, remove_scheduler

def main():
    parser = argparse.ArgumentParser(description="Hyper Video Studio CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run Pipeline
    p_run = subparsers.add_parser("run-pipeline", help="Generate a video pipeline run")
    p_run.add_argument("--topic", help="Custom video topic")
    p_run.add_argument("--hook", help="Custom viral hook")
    p_run.add_argument("--aspect", default="9:16", help="Aspect ratio (9:16, 16:9, 1:1, etc.)")
    p_run.add_argument("--theme", default="cyber_cyan", help="Theme key")

    # Dashboard
    p_dash = subparsers.add_parser("dashboard", help="Start web dashboard server")
    p_dash.add_argument("--host", default="0.0.0.0", help="Host binding")
    p_dash.add_argument("--port", type=int, default=8585, help="Port binding")

    # Scheduler
    p_sched = subparsers.add_parser("scheduler", help="Manage automated cron / launchd scheduler")
    p_sched.add_argument("--status", action="store_true", help="View current scheduler status")
    p_sched.add_argument("--install", action="store_true", help="Install daily recurring schedule")
    p_sched.add_argument("--remove", action="store_true", help="Remove daily recurring schedule")
    p_sched.add_argument("--hour", type=int, default=10, help="Hour (0-23)")
    p_sched.add_argument("--minute", type=int, default=30, help="Minute (0-59)")

    args = parser.parse_args()

    if args.command == "run-pipeline":
        manifest = run_pipeline(
            user_topic=args.topic,
            user_hook=args.hook,
            aspect_ratio=args.aspect,
            theme=args.theme
        )
        print(f"\n🎉 Finished! Output video: {manifest['video']}")

    elif args.command == "dashboard":
        from dashboard.server import start_server
        start_server(host=args.host, port=args.port)

    elif args.command == "scheduler":
        if args.install:
            res = install_scheduler(hour=args.hour, minute=args.minute)
            print(f"✅ Scheduler installed: {res}")
        elif args.remove:
            res = remove_scheduler()
            print(f"✅ Scheduler removed: {res}")
        else:
            status = get_scheduler_status()
            print("\n⏰ Current Scheduler Status:")
            for k, v in status.items():
                print(f"  • {k}: {v}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
