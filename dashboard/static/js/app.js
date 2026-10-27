// Hyper Video Studio - Core Frontend Controller
let currentConfig = {};
let activeAspect = "9:16";
let activeTheme = "cyber_cyan";
let creationMode = "autonomous";
let ws = null;

document.addEventListener("DOMContentLoaded", () => {
    initWebSocket();
    loadStatus();
    setInterval(loadStatus, 5000);
});

function initWebSocket() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${proto}//${window.location.host}/api/ws/logs`;
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const term = document.getElementById("terminalLogs");
        term.textContent += event.data;
        term.scrollTop = term.scrollHeight;

        // Auto detect status if line contains finished
        if (event.data.includes("Production Run Completed") || event.data.includes("exited with code 0")) {
            loadStatus();
        }
    };

    ws.onclose = () => {
        setTimeout(initWebSocket, 3000);
    };
}

async function loadStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        currentConfig = data.config || {};

        // Update run state
        const statusBadge = document.getElementById("statusBadge");
        const statusText = document.getElementById("statusText");
        const btnRunNow = document.getElementById("btnRunNow");
        const btnStop = document.getElementById("btnStop");

        if (data.is_running) {
            statusBadge.className = "status-pill pill-active";
            statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 pulse-active"></span><span>RENDERING</span>`;
            btnStop.classList.remove("hidden");
            btnRunNow.classList.add("hidden");
        } else {
            statusBadge.className = "status-pill pill-idle";
            statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-slate-400"></span><span>IDLE</span>`;
            btnStop.classList.add("hidden");
            btnRunNow.classList.remove("hidden");
        }

        // Update Scheduler info
        if (data.scheduler) {
            const sched = data.scheduler;
            const schedLabel = document.getElementById("cronStatusLabel");
            const schedPill = document.getElementById("cronStatusPill");
            const schedPlatform = document.getElementById("cronPlatform");
            const schedTime = document.getElementById("cronScheduledTime");
            const logBox = document.getElementById("schedulerLogBox");

            if (sched.is_active) {
                schedPill.className = "status-pill pill-active";
                schedLabel.textContent = "SCHEDULE ACTIVE";
            } else {
                schedPill.className = "status-pill pill-idle";
                schedLabel.textContent = "SCHEDULE INACTIVE";
            }

            schedPlatform.textContent = `${sched.platform} (${sched.scheduler_type.toUpperCase()})`;
            schedTime.textContent = `${sched.schedule_time} Daily`;
            if (sched.last_log) logBox.textContent = sched.last_log;
        }

        // Render Asset Library
        renderLibrary(data.latest_jobs || []);

    } catch (e) {
        console.error("Status load error:", e);
    }
}

function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.add("hidden"));

    event.currentTarget.classList.add("active");
    const target = document.getElementById(`tab-${tabId}`);
    if (target) {
        target.classList.remove("hidden");
        if (window.Motion) {
            Motion.animate(target, { opacity: [0, 1], y: [10, 0] }, { duration: 0.25 });
        }
    }
}

function setCreationMode(mode) {
    creationMode = mode;
    const btnAuto = document.getElementById("modeAutonomous");
    const btnCustom = document.getElementById("modeCustomTopic");
    const btnScript = document.getElementById("modeScript");

    const boxAuto = document.getElementById("boxAutonomous");
    const boxCustom = document.getElementById("boxCustom");
    const boxScript = document.getElementById("boxScript");

    [btnAuto, btnCustom, btnScript].forEach(b => {
        b.className = "flex-1 py-2 px-3 text-xs font-bold rounded-lg text-slate-400";
    });
    [boxAuto, boxCustom, boxScript].forEach(b => b.classList.add("hidden"));

    if (mode === "autonomous") {
        btnAuto.className = "flex-1 py-2 px-3 text-xs font-bold rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30";
        boxAuto.classList.remove("hidden");
    } else if (mode === "custom") {
        btnCustom.className = "flex-1 py-2 px-3 text-xs font-bold rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30";
        boxCustom.classList.remove("hidden");
    } else if (mode === "script") {
        btnScript.className = "flex-1 py-2 px-3 text-xs font-bold rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30";
        boxScript.classList.remove("hidden");
    }
}

function selectAspect(aspect) {
    activeAspect = aspect;
    document.querySelectorAll(".aspect-card").forEach(c => c.classList.remove("selected"));
    event.currentTarget.classList.add("selected");
    document.getElementById("labelActiveAspect").textContent = `${aspect}`;
}

function selectTheme(theme) {
    activeTheme = theme;
    document.querySelectorAll(".theme-card").forEach(c => c.classList.remove("selected", "border-cyan-500/40", "bg-cyan-950/20"));
    event.currentTarget.classList.add("selected", "border-cyan-500/40", "bg-cyan-950/20");
}

async function triggerRun() {
    const payload = {
        aspect_ratio: activeAspect,
        theme: activeTheme
    };

    if (creationMode === "custom") {
        payload.topic = document.getElementById("customTopicInput").value.trim();
        payload.hook = document.getElementById("customHookInput").value.trim();
    } else if (creationMode === "script") {
        payload.scenes = [
            { id: "scene_1", text: document.getElementById("scene1Input").value.trim() },
            { id: "scene_2", text: document.getElementById("scene2Input").value.trim() },
            { id: "scene_3", text: document.getElementById("scene3Input").value.trim() },
            { id: "scene_4", text: document.getElementById("scene4Input").value.trim() }
        ];
    }

    try {
        const res = await fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "started") {
            loadStatus();
        }
    } catch (e) {
        alert("Failed to start run: " + e.message);
    }
}

async function stopRun() {
    await fetch("/api/stop", { method: "POST" });
    loadStatus();
}

async function saveScheduler() {
    const hour = parseInt(document.getElementById("cronHour").value) || 10;
    const minute = parseInt(document.getElementById("cronMinute").value) || 30;

    const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "install", hour, minute })
    });
    const data = await res.json();
    if (data.status === "success") {
        alert(`✅ Daily automated schedule set for ${hour}:${minute} without terminal!`);
        loadStatus();
    }
}

async function disableScheduler() {
    const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "remove" })
    });
    const data = await res.json();
    if (data.status === "success") {
        alert("✅ Daily automated scheduler removed.");
        loadStatus();
    }
}

function updateTTSForm() {
    const prov = document.getElementById("ttsProviderSelect").value;
    const edgeBox = document.getElementById("edgeVoiceBox");
    const elevenBox = document.getElementById("elevenVoiceBox");

    if (prov === "elevenlabs") {
        edgeBox.classList.add("hidden");
        elevenBox.classList.remove("hidden");
    } else {
        edgeBox.classList.remove("hidden");
        elevenBox.classList.add("hidden");
    }
}

async function saveAudioSettings() {
    const prov = document.getElementById("ttsProviderSelect").value;
    const payload = {
        audio: {
            provider: prov,
            edge_voice: document.getElementById("edgeVoiceSelect").value,
            elevenlabs_api_key: document.getElementById("elevenApiKey").value.trim(),
            elevenlabs_voice_id: document.getElementById("elevenVoiceId").value.trim()
        }
    };
    await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    alert("✅ Audio settings saved successfully!");
    loadStatus();
}

async function saveLLMSettings() {
    const payload = {
        llm: {
            provider: document.getElementById("llmProviderSelect").value,
            api_key: document.getElementById("llmApiKey").value.trim(),
            model: document.getElementById("llmModel").value.trim()
        }
    };
    await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    alert("✅ LLM model settings saved successfully!");
    loadStatus();
}

function renderLibrary(jobs) {
    const list = document.getElementById("jobsList");
    if (!jobs || jobs.length === 0) {
        list.innerHTML = `<div class="p-8 text-center text-slate-500 text-sm">No completed videos yet. Run the pipeline to produce your first video!</div>`;
        return;
    }

    list.innerHTML = jobs.map(job => {
        const folder = job.folder_name;
        const topic = job.topic || {};
        const videoName = job.video ? job.video.split("/").pop() : "";
        const thumbName = job.thumbnails && job.thumbnails["16_9"] ? job.thumbnails["16_9"].split("/").pop() : "";

        return `
            <div class="p-5 rounded-2xl bg-slate-900/40 border border-white/5 flex flex-col md:flex-row gap-5 items-start md:items-center justify-between">
                <div class="flex gap-4 items-center">
                    <div class="w-28 h-16 rounded-lg bg-black overflow-hidden flex-shrink-0 border border-white/10">
                        ${thumbName ? `<img src="/api/media/${folder}/${thumbName}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-xs text-slate-500">Preview</div>`}
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-mono font-bold text-cyan-400">// ${topic.category || 'Tech'} //</span>
                            <span class="text-xs text-slate-500 font-mono">${job.created_at || ''}</span>
                        </div>
                        <h4 class="text-sm font-bold text-slate-100">${topic.topic || 'Engineering Reel'}</h4>
                        <p class="text-xs text-slate-400 line-clamp-1">${topic.hook || ''}</p>
                    </div>
                </div>

                <div class="flex items-center gap-3 w-full md:w-auto justify-end">
                    ${videoName ? `
                        <a href="/api/media/${folder}/${videoName}" target="_blank" class="btn-primary text-xs">
                            <i data-lucide="play" class="w-3.5 h-3.5"></i>
                            <span>Watch</span>
                        </a>
                        <a href="/api/media/${folder}/${videoName}" download class="btn-secondary text-xs">
                            <i data-lucide="download" class="w-3.5 h-3.5"></i>
                            <span>MP4</span>
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }).join("");

    if (window.lucide) lucide.createIcons();
}
