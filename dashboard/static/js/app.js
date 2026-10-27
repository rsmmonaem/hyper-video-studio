// Hyper Video Studio - Multi-Project & Modular Controller
let allProjects = [];
let currentProjectId = null;
let currentProjectData = null;
let activeAspect = "9:16";
let activeTheme = "cyber_cyan";
let creationMode = "autonomous";
let ws = null;
let stepTimerInterval = null;
let currentRunningStep = null;
let stepStartTime = 0;

document.addEventListener("DOMContentLoaded", () => {
    initWebSocket();
    
    // Check URL param ?project=...
    const urlParams = new URLSearchParams(window.location.search);
    const projParam = urlParams.get("project");
    
    loadProjectsList(projParam);
    setInterval(() => {
        if (currentProjectId) {
            loadProjectStudio(currentProjectId, true);
        } else {
            loadProjectsList(null, true);
        }
    }, 6000);
});

function initWebSocket() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${proto}//${window.location.host}/api/ws/logs`;
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const text = event.data;
        const term = document.getElementById("terminalLogs");
        if (term) {
            term.textContent += text;
            term.scrollTop = term.scrollHeight;
        }

        // Parse Step Markers
        handleStepLog(text);

        if (text.includes("PIPELINE_COMPLETE") || text.includes("Process exited with code 0")) {
            stopStepTimer();
            setStudioIdle();
            if (currentProjectId) loadProjectStudio(currentProjectId);
        }
    };

    ws.onclose = () => {
        setTimeout(initWebSocket, 3000);
    };
}

function handleStepLog(line) {
    if (line.includes("STEP_START:")) {
        const match = line.match(/STEP_START:\s*(\d+)\s*\|\s*(.*)/);
        if (match) {
            const stepNum = match[1];
            markStepRunning(stepNum);
        }
    } else if (line.includes("STEP_DONE:")) {
        const match = line.match(/STEP_DONE:\s*(\d+)\s*\|\s*(.*)/);
        if (match) {
            const stepNum = match[1];
            const duration = match[2];
            markStepDone(stepNum, duration);
        }
    }
}

function resetStepTracker() {
    for (let i = 1; i <= 5; i++) {
        const card = document.getElementById(`stepCard${i}`);
        const badge = document.getElementById(`stepBadge${i}`);
        const timeEl = document.getElementById(`stepTime${i}`);
        if (card) {
            card.classList.remove("running", "completed");
            card.classList.add("border-white/5", "bg-slate-900/40");
        }
        if (badge) {
            badge.className = "status-pill text-[10px] py-0.5 px-2 bg-slate-800 text-slate-400";
            badge.textContent = "Idle";
        }
        if (timeEl) timeEl.textContent = "--";
    }
    document.getElementById("pipelineTotalTime").textContent = "";
}

function markStepRunning(stepNum) {
    stopStepTimer();
    currentRunningStep = stepNum;
    stepStartTime = Date.now();

    const card = document.getElementById(`stepCard${stepNum}`);
    const badge = document.getElementById(`stepBadge${stepNum}`);
    const timeEl = document.getElementById(`stepTime${stepNum}`);

    if (card) {
        card.classList.remove("completed");
        card.classList.add("running");
    }
    if (badge) {
        badge.className = "status-pill text-[10px] py-0.5 px-2 bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";
        badge.innerHTML = `<span class="animate-spin inline-block mr-1">⚙️</span> Running`;
    }

    stepTimerInterval = setInterval(() => {
        const elapsed = ((Date.now() - stepStartTime) / 1000).toFixed(1);
        if (timeEl) timeEl.textContent = `${elapsed}s`;
    }, 200);
}

function markStepDone(stepNum, duration) {
    if (currentRunningStep == stepNum) {
        stopStepTimer();
    }
    const card = document.getElementById(`stepCard${stepNum}`);
    const badge = document.getElementById(`stepBadge${stepNum}`);
    const timeEl = document.getElementById(`stepTime${stepNum}`);

    if (card) {
        card.classList.remove("running");
        card.classList.add("completed");
    }
    if (badge) {
        badge.className = "status-pill text-[10px] py-0.5 px-2 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
        badge.innerHTML = `✓ Done`;
    }
    if (timeEl && duration) {
        timeEl.textContent = duration;
    }
}

function stopStepTimer() {
    if (stepTimerInterval) {
        clearInterval(stepTimerInterval);
        stepTimerInterval = null;
    }
    currentRunningStep = null;
}

// ==========================================
// PROJECTS HUB CONTROLLER
// ==========================================

async function loadProjectsList(autoOpenProjectId = null, silent = false) {
    try {
        const res = await fetch("/api/projects");
        const data = await res.json();
        allProjects = data.projects || [];

        const countLabel = document.getElementById("projectsCountLabel");
        if (countLabel) countLabel.textContent = `${allProjects.length} Channels Configured`;

        renderProjectsGrid(allProjects);

        const switcher = document.getElementById("projectSwitcherSelect");
        if (switcher) {
            switcher.innerHTML = allProjects.map(p => 
                `<option value="${p.id}" ${p.id === currentProjectId ? 'selected' : ''}>${p.name} (${p.aspect_ratio})</option>`
            ).join("");
        }

        if (autoOpenProjectId && !silent) {
            openProjectStudio(autoOpenProjectId);
        }
    } catch (e) {
        console.error("Failed to load projects:", e);
    }
}

function renderProjectsGrid(projects) {
    const grid = document.getElementById("projectsGrid");
    if (!grid) return;

    if (!projects || projects.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full p-12 text-center glass-panel">
                <i data-lucide="folder-plus" class="w-12 h-12 mx-auto text-cyan-400 mb-3 opacity-60"></i>
                <h3 class="text-lg font-bold text-slate-200">No Projects Found</h3>
                <p class="text-sm text-slate-400 mt-1 mb-4">Create your first channel to get started.</p>
                <button class="btn-primary" onclick="openNewProjectModal()">Create Channel Project</button>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    grid.innerHTML = projects.map(p => {
        const ratioBadge = p.aspect_ratio || "9:16";
        const cat = p.category || "General";
        const vCount = p.video_count || 0;
        const author = p.branding?.author || "Creator";
        const thumbUrl = p.latest_thumbnail || "/output/test_thumb_16_9.jpg";

        return `
            <div class="glass-panel overflow-hidden flex flex-col justify-between group hover:border-cyan-500/50 transition-all duration-300">
                <div class="aspect-video w-full bg-slate-950 relative overflow-hidden border-b border-white/5">
                    <img src="${thumbUrl}" alt="${p.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='/static/placeholder.jpg'">
                    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30"></div>
                    
                    <div class="absolute top-3 left-3 flex gap-2">
                        <span class="status-pill pill-active text-[11px] font-bold">${ratioBadge}</span>
                        <span class="status-pill pill-idle text-[11px] bg-black/60 backdrop-blur-md">${cat}</span>
                    </div>

                    <div class="absolute bottom-3 left-3 right-3 flex justify-between items-end text-xs font-mono">
                        <span class="text-cyan-300 font-bold">${vCount} Videos</span>
                        <span class="text-slate-300 text-[10px]">Host: ${author}</span>
                    </div>
                </div>

                <div class="p-5 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                        <h3 class="text-lg font-extrabold text-white group-hover:text-cyan-300 transition-colors line-clamp-1">${p.name}</h3>
                        <p class="text-xs text-slate-400 line-clamp-2 mt-1">${p.description || 'Autonomous video studio'}</p>
                    </div>

                    <div class="pt-3 border-t border-white/5 flex items-center justify-between gap-3">
                        <button class="btn-primary flex-1 justify-center text-xs py-2.5" onclick="openProjectStudio('${p.id}')">
                            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            <span>Open Studio</span>
                        </button>
                        <button class="btn-secondary py-2.5 px-3 text-xs text-red-400 hover:text-red-300 hover:border-red-500/40" onclick="deleteProjectPrompt('${p.id}', '${p.name}')" title="Delete Project">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    if (window.lucide) lucide.createIcons();
}

// ==========================================
// STUDIO CONTROLLER (SCOPED TO PROJECT)
// ==========================================

async function openProjectStudio(projectId) {
    currentProjectId = projectId;
    window.history.pushState({}, "", `?project=${projectId}`);

    const viewHub = document.getElementById("viewProjectsHub");
    const viewStudio = document.getElementById("viewStudio");

    viewHub.classList.add("hidden");
    viewStudio.classList.remove("hidden");

    if (window.Motion) {
        Motion.animate(viewStudio, { opacity: [0, 1], y: [15, 0] }, { duration: 0.3 });
    }

    await loadProjectStudio(projectId);
}

function exitToProjectsHub() {
    currentProjectId = null;
    window.history.pushState({}, "", window.location.pathname);

    document.getElementById("viewStudio").classList.add("hidden");
    const viewHub = document.getElementById("viewProjectsHub");
    viewHub.classList.remove("hidden");

    if (window.Motion) {
        Motion.animate(viewHub, { opacity: [0, 1], y: [15, 0] }, { duration: 0.3 });
    }

    loadProjectsList();
}

function switchProjectDirectly(projectId) {
    if (projectId) {
        openProjectStudio(projectId);
    }
}

async function loadProjectStudio(projectId, silent = false) {
    try {
        const res = await fetch(`/api/projects/${projectId}`);
        const data = await res.json();
        if (data.status !== "success" || !data.project) return;

        currentProjectData = data.project;

        // Header & Branding Profile
        document.getElementById("studioProjectTitle").textContent = currentProjectData.name;
        document.getElementById("studioAspectBadge").textContent = currentProjectData.aspect_ratio || "9:16";
        document.getElementById("studioProjectSubtitle").textContent = currentProjectData.description || "";
        
        const author = currentProjectData.branding?.author || "Creator";
        const brand = currentProjectData.branding?.brand_name || currentProjectData.name;
        const handle = currentProjectData.branding?.handle || `@${currentProjectData.id}`;
        const cat = currentProjectData.category || "Software Architecture";

        document.getElementById("studioAuthorTag").textContent = `Author: ${author} • ${brand}`;
        document.getElementById("labelCurrentProject").textContent = brand;
        document.getElementById("labelCurrentAuthor").textContent = author;
        document.getElementById("labelActiveAspect").textContent = currentProjectData.aspect_ratio || "9:16";
        document.getElementById("labelCurrentVoice").textContent = currentProjectData.voice || "bn-IN-BashkarNeural";
        document.getElementById("labelCurrentBrand").textContent = handle;

        // Branding Drawer Inputs
        document.getElementById("brandAuthorInput").value = author;
        document.getElementById("brandNameInput").value = brand;
        document.getElementById("brandHandleInput").value = handle;
        document.getElementById("brandCategoryInput").value = cat;

        // Select aspect & theme
        activeAspect = currentProjectData.aspect_ratio || "9:16";
        activeTheme = currentProjectData.theme || "cyber_cyan";

        selectAspect(activeAspect, null, false);
        selectTheme(activeTheme, null, false);

        // Restore Saved Draft Memory
        const draft = currentProjectData.draft || {};
        if (draft.topic) document.getElementById("customTopicInput").value = draft.topic;
        if (draft.hook) document.getElementById("customHookInput").value = draft.hook;
        if (draft.scene_1) document.getElementById("scene1Input").value = draft.scene_1;
        if (draft.scene_2) document.getElementById("scene2Input").value = draft.scene_2;
        if (draft.scene_3) document.getElementById("scene3Input").value = draft.scene_3;
        if (draft.scene_4) document.getElementById("scene4Input").value = draft.scene_4;
        if (draft.mode) setCreationMode(draft.mode);

        // Restore LLM Settings
        const llm = currentProjectData.llm || {};
        const llmCheck = document.getElementById("llmEnabledCheckbox");
        if (llmCheck) {
            llmCheck.checked = !!llm.enabled;
            toggleLLMFields();
        }
        if (llm.provider) document.getElementById("llmProviderSelect").value = llm.provider;
        if (llm.api_key) document.getElementById("llmApiKey").value = llm.api_key;

        // Restore Audio Settings
        const audio = currentProjectData.audio || {};
        if (audio.provider) document.getElementById("ttsProviderSelect").value = audio.provider;
        if (audio.edge_voice) document.getElementById("edgeVoiceSelect").value = audio.edge_voice;

        // Switcher dropdown value
        const switcher = document.getElementById("projectSwitcherSelect");
        if (switcher) switcher.value = projectId;

        // Thumbnails tab preview
        const img16 = document.getElementById("imgThumb16");
        const img9 = document.getElementById("imgThumb9");
        if (currentProjectData.jobs && currentProjectData.jobs.length > 0) {
            const latest = currentProjectData.jobs[0];
            const folder = latest.folder_name;
            if (img16) img16.src = `/api/projects/${projectId}/media/${folder}/thumbnail_16_9.jpg`;
            if (img9) img9.src = `/api/projects/${projectId}/media/${folder}/thumbnail_9_16.jpg`;
        }

        // Render project library
        renderLibrary(currentProjectData.jobs || []);

    } catch (e) {
        console.error("Failed to load project studio:", e);
    }
}

function toggleBrandingDrawer() {
    const drawer = document.getElementById("brandingDrawer");
    if (drawer.classList.contains("hidden")) {
        drawer.classList.remove("hidden");
        if (window.Motion) {
            Motion.animate(drawer, { opacity: [0, 1], y: [-10, 0] }, { duration: 0.25 });
        }
    } else {
        drawer.classList.add("hidden");
    }
}

async function saveChannelProfile() {
    if (!currentProjectId) return;
    const author = document.getElementById("brandAuthorInput").value.trim();
    const brandName = document.getElementById("brandNameInput").value.trim();
    const handle = document.getElementById("brandHandleInput").value.trim();
    const category = document.getElementById("brandCategoryInput").value.trim();

    const updates = {
        category: category,
        branding: {
            author: author,
            brand_name: brandName,
            handle: handle,
            brand_tagline: category
        }
    };

    try {
        const res = await fetch(`/api/projects/${currentProjectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updates)
        });
        const data = await res.json();
        if (data.status === "success") {
            const toast = document.getElementById("brandSaveToast");
            toast.style.opacity = "1";
            setTimeout(() => { toast.style.opacity = "0"; }, 2000);
            loadProjectStudio(currentProjectId, true);
        }
    } catch (e) {
        alert("Failed to save channel profile: " + e.message);
    }
}

async function autoSaveDraft() {
    if (!currentProjectId) return;
    const draft = {
        mode: creationMode,
        topic: document.getElementById("customTopicInput").value.trim(),
        hook: document.getElementById("customHookInput").value.trim(),
        scene_1: document.getElementById("scene1Input").value.trim(),
        scene_2: document.getElementById("scene2Input").value.trim(),
        scene_3: document.getElementById("scene3Input").value.trim(),
        scene_4: document.getElementById("scene4Input").value.trim()
    };

    fetch(`/api/projects/${currentProjectId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft })
    }).catch(console.error);
}

function pickQuickTopic(topic, hook) {
    document.getElementById("customTopicInput").value = topic;
    document.getElementById("customHookInput").value = hook;
    setCreationMode("custom");
    autoSaveDraft();
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

    autoSaveDraft();
}

function selectAspect(aspect, el, persist = true) {
    activeAspect = aspect;
    document.querySelectorAll(".aspect-card").forEach(c => {
        c.classList.remove("selected", "border-cyan-400");
    });
    const target = el || document.querySelector(`.aspect-card[data-aspect="${aspect}"]`);
    if (target) {
        target.classList.add("selected", "border-cyan-400");
    }
    const label = document.getElementById("labelActiveAspect");
    if (label) label.textContent = `${aspect}`;

    if (persist && currentProjectId) {
        fetch(`/api/projects/${currentProjectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ aspect_ratio: aspect })
        }).catch(console.error);
    }
}

function selectTheme(theme, el, persist = true) {
    activeTheme = theme;
    document.querySelectorAll(".theme-card").forEach(c => {
        c.classList.remove("selected", "border-cyan-400", "border-orange-400", "bg-cyan-950/40", "bg-orange-950/30", "shadow-lg");
        c.classList.add("border-white/5", "bg-slate-900/40");
    });
    const target = el || document.querySelector(`.theme-card[data-theme="${theme}"]`);
    if (target) {
        target.classList.remove("border-white/5", "bg-slate-900/40");
        target.classList.add("selected", "border-cyan-400", "bg-cyan-950/40", "shadow-lg");
    }
    const label = document.getElementById("labelCurrentTheme");
    if (label) {
        const names = {
            "cyber_cyan": "Cyber Cyan",
            "fire_ember": "Fire Ember",
            "matrix_terminal": "Matrix Terminal",
            "tokyo_neon": "Tokyo Midnight",
            "clean_minimal": "Studio Obsidian"
        };
        label.textContent = names[theme] || theme;
    }

    if (persist && currentProjectId) {
        fetch(`/api/projects/${currentProjectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme: theme })
        }).catch(console.error);
    }
}

// ==========================================
// MODULAR RUN EXECUTOR (4 DISTINCT MODES)
// ==========================================

async function triggerModularRun(action = "full") {
    resetStepTracker();
    setStudioRunning();

    const payload = {
        project_id: currentProjectId,
        action: action,
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
        if (data.status !== "started") {
            alert("Could not start run: " + JSON.stringify(data));
            setStudioIdle();
        }
    } catch (e) {
        alert("Failed to start run: " + e.message);
        setStudioIdle();
    }
}

function setStudioRunning() {
    const badge = document.getElementById("statusBadge");
    const statusText = document.getElementById("statusText");
    const btnStop = document.getElementById("btnStop");

    badge.className = "status-pill pill-active";
    statusText.textContent = "RUNNING";
    btnStop.classList.remove("hidden");
}

function setStudioIdle() {
    const badge = document.getElementById("statusBadge");
    const statusText = document.getElementById("statusText");
    const btnStop = document.getElementById("btnStop");

    badge.className = "status-pill pill-idle";
    statusText.textContent = "IDLE";
    btnStop.classList.add("hidden");
}

async function stopRun() {
    await fetch("/api/stop", { method: "POST" });
    setStudioIdle();
    stopStepTimer();
}

function toggleLLMFields() {
    const check = document.getElementById("llmEnabledCheckbox");
    const box = document.getElementById("llmFieldsBox");
    if (check.checked) {
        box.classList.remove("opacity-50", "pointer-events-none");
    } else {
        box.classList.add("opacity-50", "pointer-events-none");
    }
}

async function saveLLMSettings() {
    if (!currentProjectId) return;
    const isEnabled = document.getElementById("llmEnabledCheckbox").checked;
    const provider = document.getElementById("llmProviderSelect").value;
    const apiKey = document.getElementById("llmApiKey").value.trim();

    const updates = {
        llm: {
            enabled: isEnabled,
            provider: provider,
            api_key: apiKey
        }
    };

    try {
        await fetch(`/api/projects/${currentProjectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updates)
        });
        alert("LLM settings saved to project!");
    } catch (e) {
        alert("Failed to save LLM settings: " + e.message);
    }
}

async function saveAudioSettings() {
    if (!currentProjectId) return;
    const provider = document.getElementById("ttsProviderSelect").value;
    const voice = document.getElementById("edgeVoiceSelect").value;

    const updates = {
        voice: voice,
        audio: {
            provider: provider,
            edge_voice: voice
        }
    };

    try {
        await fetch(`/api/projects/${currentProjectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updates)
        });
        document.getElementById("labelCurrentVoice").textContent = voice;
        alert("Voice settings saved to project!");
    } catch (e) {
        alert("Failed to save audio settings: " + e.message);
    }
}

function renderLibrary(jobs) {
    const list = document.getElementById("jobsList");
    if (!list) return;

    if (!jobs || jobs.length === 0) {
        list.innerHTML = `<div class="p-8 text-center text-slate-500 text-sm glass-panel">No completed videos in this project yet. Click 'Full Production Run' to produce your first video!</div>`;
        return;
    }

    list.innerHTML = jobs.map(job => {
        const folder = job.folder_name;
        const topic = job.topic || {};
        const videoName = job.video ? job.video.split("/").pop() : "";
        const thumbName = job.thumbnails && job.thumbnails["16_9"] ? job.thumbnails["16_9"].split("/").pop() : "";
        const mediaEndpoint = currentProjectId ? `/api/projects/${currentProjectId}/media/${folder}` : `/api/media/${folder}`;

        return `
            <div class="p-5 rounded-2xl bg-slate-900/40 border border-white/5 flex flex-col md:flex-row gap-5 items-start md:items-center justify-between">
                <div class="flex gap-4 items-center">
                    <div class="w-28 h-16 rounded-lg bg-black overflow-hidden flex-shrink-0 border border-white/10">
                        ${thumbName ? `<img src="${mediaEndpoint}/${thumbName}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-xs text-slate-500">Preview</div>`}
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-mono font-bold text-cyan-400">// ${topic.category || 'Architecture'} //</span>
                            <span class="text-xs text-slate-500 font-mono">${job.created_at || ''}</span>
                        </div>
                        <h4 class="text-sm font-bold text-slate-100">${topic.topic || 'Engineering Reel'}</h4>
                        <p class="text-xs text-slate-400 line-clamp-1">${topic.hook || ''}</p>
                    </div>
                </div>

                <div class="flex items-center gap-2.5 w-full md:w-auto justify-end flex-wrap">
                    ${thumbName ? `
                        <a href="${mediaEndpoint}/${thumbName}" target="_blank" class="btn-secondary text-xs py-2 px-3 text-purple-300">
                            <i data-lucide="image" class="w-3.5 h-3.5"></i>
                            <span>Thumbnail</span>
                        </a>
                    ` : ''}
                    ${videoName ? `
                        <a href="${mediaEndpoint}/${videoName}" target="_blank" class="btn-primary text-xs py-2 px-3">
                            <i data-lucide="play" class="w-3.5 h-3.5"></i>
                            <span>Watch</span>
                        </a>
                        <a href="${mediaEndpoint}/${videoName}" download class="btn-secondary text-xs py-2 px-3">
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

// ==========================================
// ULTRA-SIMPLE PROJECT CREATION MODAL
// ==========================================

function openNewProjectModal() {
    const modal = document.getElementById("modalNewProject");
    modal.classList.remove("hidden");
    const input = document.getElementById("newProjName");
    input.value = "";
    setTimeout(() => input.focus(), 50);
}

function closeNewProjectModal() {
    document.getElementById("modalNewProject").classList.add("hidden");
}

async function submitCreateProject() {
    const name = document.getElementById("newProjName").value.trim();
    if (!name) return alert("Please enter a project name.");

    const payload = {
        name: name,
        author: document.getElementById("newProjAuthor")?.value.trim() || "",
        aspect_ratio: document.getElementById("newProjAspect")?.value || "9:16",
        theme: document.getElementById("newProjTheme")?.value || "cyber_cyan"
    };

    try {
        const res = await fetch("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "success" && data.project) {
            closeNewProjectModal();
            // Automatically open newly created studio!
            await loadProjectsList(null, true);
            openProjectStudio(data.project.id);
        }
    } catch (e) {
        alert("Failed to create project: " + e.message);
    }
}

async function deleteProjectPrompt(pid, pname) {
    if (confirm(`Are you sure you want to delete project '${pname}'? All generated videos inside this project will be removed.`)) {
        await fetch(`/api/projects/${pid}`, { method: "DELETE" });
        loadProjectsList();
    }
}