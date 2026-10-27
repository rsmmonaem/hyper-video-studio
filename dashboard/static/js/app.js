// Hyper Video Studio - Multi-Project Controller
let allProjects = [];
let currentProjectId = null;
let currentProjectData = null;
let activeAspect = "9:16";
let activeTheme = "cyber_cyan";
let creationMode = "autonomous";
let ws = null;

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
        const term = document.getElementById("terminalLogs");
        if (term) {
            term.textContent += event.data;
            term.scrollTop = term.scrollHeight;
        }

        if (event.data.includes("Production Run Completed") || event.data.includes("exited with code 0")) {
            if (currentProjectId) loadProjectStudio(currentProjectId);
        }
    };

    ws.onclose = () => {
        setTimeout(initWebSocket, 3000);
    };
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
        if (countLabel) countLabel.textContent = `${allProjects.length} Projects Available`;

        // Render projects grid
        renderProjectsGrid(allProjects);

        // Update top project switcher select
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
                <button class="btn-primary" onclick="openNewProjectModal()">Create Project</button>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    grid.innerHTML = projects.map(p => {
        const ratioBadge = p.aspect_ratio || "9:16";
        const cat = p.category || "General";
        const vCount = p.video_count || 0;
        const theme = p.theme || "cyber_cyan";
        const thumbUrl = p.latest_thumbnail || "/output/test_thumb_16_9.jpg";

        return `
            <div class="glass-panel overflow-hidden flex flex-col justify-between group hover:border-cyan-500/50 transition-all duration-300">
                <!-- Thumbnail Cover Preview -->
                <div class="aspect-video w-full bg-slate-950 relative overflow-hidden border-b border-white/5">
                    <img src="${thumbUrl}" alt="${p.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='/static/placeholder.jpg'">
                    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30"></div>
                    
                    <div class="absolute top-3 left-3 flex gap-2">
                        <span class="status-pill pill-active text-[11px] font-bold">${ratioBadge}</span>
                        <span class="status-pill pill-idle text-[11px] bg-black/60 backdrop-blur-md">${cat}</span>
                    </div>

                    <div class="absolute bottom-3 left-3 right-3 flex justify-between items-end text-xs font-mono">
                        <span class="text-cyan-300 font-bold">${vCount} Videos</span>
                        <span class="text-slate-400 text-[10px]">${p.voice || 'BashkarNeural'}</span>
                    </div>
                </div>

                <!-- Info Body -->
                <div class="p-5 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                        <h3 class="text-lg font-extrabold text-white group-hover:text-cyan-300 transition-colors line-clamp-1">${p.name}</h3>
                        <p class="text-xs text-slate-400 line-clamp-2 mt-1">${p.description || 'Autonomous video generation project'}</p>
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

        // Update studio header
        document.getElementById("studioProjectTitle").textContent = currentProjectData.name;
        document.getElementById("studioAspectBadge").textContent = currentProjectData.aspect_ratio || "9:16";
        document.getElementById("studioProjectSubtitle").textContent = currentProjectData.description || "";
        document.getElementById("labelCurrentProject").textContent = currentProjectData.name;
        document.getElementById("labelActiveAspect").textContent = currentProjectData.aspect_ratio || "9:16";
        document.getElementById("labelCurrentVoice").textContent = currentProjectData.voice || "bn-IN-BashkarNeural";
        document.getElementById("labelCurrentBrand").textContent = currentProjectData.branding?.brand_name || "FTLTD";

        // Select aspect & theme
        activeAspect = currentProjectData.aspect_ratio || "9:16";
        activeTheme = currentProjectData.theme || "cyber_cyan";

        selectAspect(activeAspect);
        selectTheme(activeTheme);

        // Set switcher select value
        const switcher = document.getElementById("projectSwitcherSelect");
        if (switcher) switcher.value = projectId;

        // Render project library
        renderLibrary(currentProjectData.jobs || []);

    } catch (e) {
        console.error("Failed to load project studio:", e);
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

function selectAspect(aspect, el) {
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
}

function selectTheme(theme, el) {
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
}

async function triggerRun() {
    const payload = {
        project_id: currentProjectId,
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
            const btnRun = document.getElementById("btnRunNow");
            const btnStop = document.getElementById("btnStop");
            btnRun.classList.add("hidden");
            btnStop.classList.remove("hidden");
        }
    } catch (e) {
        alert("Failed to start run: " + e.message);
    }
}

async function stopRun() {
    await fetch("/api/stop", { method: "POST" });
    const btnRun = document.getElementById("btnRunNow");
    const btnStop = document.getElementById("btnStop");
    btnStop.classList.add("hidden");
    btnRun.classList.remove("hidden");
}

function renderLibrary(jobs) {
    const list = document.getElementById("jobsList");
    if (!list) return;

    if (!jobs || jobs.length === 0) {
        list.innerHTML = `<div class="p-8 text-center text-slate-500 text-sm glass-panel">No completed videos in this project yet. Click 'Run Now' to produce your first video!</div>`;
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

                <div class="flex items-center gap-3 w-full md:w-auto justify-end">
                    ${videoName ? `
                        <a href="${mediaEndpoint}/${videoName}" target="_blank" class="btn-primary text-xs">
                            <i data-lucide="play" class="w-3.5 h-3.5"></i>
                            <span>Watch</span>
                        </a>
                        <a href="${mediaEndpoint}/${videoName}" download class="btn-secondary text-xs">
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

// Modal actions
function openNewProjectModal() {
    document.getElementById("modalNewProject").classList.remove("hidden");
}

function closeNewProjectModal() {
    document.getElementById("modalNewProject").classList.add("hidden");
}

async function submitCreateProject() {
    const name = document.getElementById("newProjName").value.trim();
    if (!name) return alert("Please enter a project name.");

    const payload = {
        name: name,
        category: document.getElementById("newProjCategory").value.trim() || "Software Architecture",
        aspect_ratio: document.getElementById("newProjAspect").value,
        theme: document.getElementById("newProjTheme").value,
        voice: document.getElementById("newProjVoice").value
    };

    try {
        const res = await fetch("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "success") {
            closeNewProjectModal();
            loadProjectsList(data.project.id);
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
