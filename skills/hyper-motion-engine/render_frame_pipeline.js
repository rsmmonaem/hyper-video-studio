#!/usr/bin/env node
/**
 * Hyper Video Studio - Universal Deterministic Frame Renderer
 * Supports:
 * - Frame-by-frame video rendering with seek-safe GSAP timelines
 * - High-CTR Broadcast Thumbnail capture (16:9, 9:16, 1:1, etc.)
 * - Cross-platform Chrome / Chromium auto-discovery (Mac, Linux, Docker, Windows)
 */

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

// Discover Puppeteer-core
let puppeteer;
try {
    puppeteer = require("puppeteer-core");
} catch (e) {
    try {
        puppeteer = require(path.join(__dirname, "../../node_modules/puppeteer-core"));
    } catch (err) {
        console.error("❌ puppeteer-core not found. Run 'npm install' in the project directory.");
        process.exit(1);
    }
}

function findChromeExecutable() {
    if (process.env.CHROME_BIN && fs.existsSync(process.env.CHROME_BIN)) {
        return process.env.CHROME_BIN;
    }
    const candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    ];
    for (const c of candidates) {
        if (fs.existsSync(c)) return c;
    }
    return null;
}

function findFFmpegExecutable() {
    if (process.env.FFMPEG_PATH && fs.existsSync(process.env.FFMPEG_PATH)) {
        return process.env.FFMPEG_PATH;
    }
    const candidates = [
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/usr/bin/ffmpeg",
        "ffmpeg"
    ];
    for (const c of candidates) {
        if (fs.existsSync(c)) return c;
    }
    return "ffmpeg";
}

async function renderThumbnail(htmlPath, outputPath, width, height) {
    const chromePath = findChromeExecutable();
    if (!chromePath) throw new Error("Chrome/Chromium executable not found.");

    const browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: "new",
        args: [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-first-run"
        ]
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: parseInt(width), height: parseInt(height), deviceScaleFactor: 1 });
        const html = fs.readFileSync(htmlPath, "utf-8");
        await page.setContent(html, { waitUntil: "networkidle0" });
        await page.screenshot({ path: outputPath, type: "jpeg", quality: 95 });
        console.log(`✅ Thumbnail captured: ${outputPath}`);
    } finally {
        await browser.close();
    }
}

async function renderVideo(htmlPath, outputMp4, width, height, duration, fps = 24) {
    const chromePath = findChromeExecutable();
    const ffmpegPath = findFFmpegExecutable();

    if (!chromePath) throw new Error("Chrome/Chromium executable not found.");

    const w = parseInt(width);
    const h = parseInt(height);
    const totalFrames = Math.round(parseFloat(duration) * fps);

    console.log(`🎬 Initializing Chromium Render: ${w}x${h} @ ${fps}fps (${totalFrames} frames)...`);

    const browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: "new",
        args: [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote"
        ]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });

    const htmlContent = fs.readFileSync(htmlPath, "utf-8");
    await page.setContent(htmlContent, { waitUntil: "networkidle0" });

    // Setup FFmpeg image2pipe process
    const ffmpeg = spawn(ffmpegPath, [
        "-y",
        "-f", "image2pipe",
        "-vcodec", "png",
        "-r", String(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        outputMp4
    ]);

    ffmpeg.stderr.on("data", () => {});

    console.log(`🚀 Streaming ${totalFrames} frames to FFmpeg pipeline...`);

    for (let frame = 0; frame < totalFrames; frame++) {
        const t = frame / fps;

        // Seek GSAP timeline deterministically
        await page.evaluate((timeSec) => {
            if (window.masterTl) {
                window.masterTl.pause();
                window.masterTl.seek(timeSec);
            }
        }, t);

        const buffer = await page.screenshot({ type: "png", omitBackground: false });
        ffmpeg.stdin.write(buffer);

        if (frame % 90 === 0 || frame === totalFrames - 1) {
            const pct = Math.round((frame / totalFrames) * 100);
            console.log(`  Frame ${frame}/${totalFrames} (${pct}%)`);
        }
    }

    ffmpeg.stdin.end();

    await new Promise((resolve, reject) => {
        ffmpeg.on("close", (code) => {
            if (code === 0) resolve();
            else reject(new Error(`FFmpeg exited with code ${code}`));
        });
    });

    await browser.close();
    console.log(`✅ Raw video compiled: ${outputMp4}`);
}

// CLI Argument Dispatcher
(async () => {
    const args = process.argv.slice(2);
    const mode = args[0]; // 'thumbnail' or 'video'

    try {
        if (mode === "thumbnail") {
            const [_, htmlPath, outputPath, w, h] = args;
            await renderThumbnail(htmlPath, outputPath, w, h);
        } else if (mode === "video") {
            const [_, htmlPath, outputMp4, w, h, duration, fps] = args;
            await renderVideo(htmlPath, outputMp4, w, h, duration, parseInt(fps || 24));
        } else {
            console.log("Usage: node render_frame_pipeline.js <thumbnail|video> <args...>");
            process.exit(1);
        }
    } catch (err) {
        console.error("❌ Render error:", err.message);
        process.exit(1);
    }
})();
