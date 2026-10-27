---
name: cron-automator
description: Zero-terminal background automation scheduler for macOS LaunchAgents and Linux/VPS Crontab.
---

# Cron Automator Skill

Enables end users to schedule, modify, and monitor daily automated video production directly from the web dashboard without using a terminal.

## Architecture
- **macOS**: Manages `~/Library/LaunchAgents/com.hypervideostudio.daily.plist` via `launchctl load/unload`.
- **Linux / VPS**: Directly manages user crontab (`crontab -l` / `crontab -`).
- **One-Click Actions**:
  - Install daily schedule (e.g. 10:30 AM).
  - Remove / disable schedule.
  - View real-time scheduler execution log.
