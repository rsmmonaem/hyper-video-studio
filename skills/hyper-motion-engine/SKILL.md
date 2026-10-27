---
name: hyper-motion-engine
description: Deterministic 60fps Chromium frame-by-frame motion graphics rendering engine using GSAP and FFmpeg pipes.
---

# Hyper Motion Engine Skill

This skill implements seek-safe, deterministic motion graphics rendering that works identically across macOS, Linux VPS, Docker, and Windows.

## Core Rules
1. **Never use native CSS transitions (`transition: all ...`)**: CSS transitions run on the browser wall clock rather than the render timeline, causing dropped frames during background capture.
2. **Drive all animations with GSAP paused timelines**:
   ```js
   window.masterTl = gsap.timeline({ paused: true });
   ```
3. **Deterministic Frame Capture**: The pipeline calls `window.masterTl.seek(frame / fps)` and pipes raw screenshot buffers into FFmpeg `image2pipe`:
   ```bash
   ffmpeg -y -f image2pipe -vcodec png -r 24 -i - -c:v libx264 -pix_fmt yuv420p output.mp4
   ```
4. **Adaptive Aspect Ratios**: Supports `9:16` (1080x1920), `16:9` (1920x1080), `1:1` (1080x1080), `4:5` (1080x1350), `4:3` (1440x1080), and `3:4` (1080x1440) dynamically.
