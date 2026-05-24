/* WebAI Chat Setup Wizard - Frontend Logic */

let currentStep = 1;
const totalSteps = 10;
let isInstalled = false;
let wizardData = {
    mode: "local",
    server: { host: "0.0.0.0", port: 8000, username: "", password: "" },
    ollama: { url: "http://localhost:11434", model: "qwen2.5:3b", embedding_model: "all-MiniLM-L6-v2" },
    cloud: { provider: "openai", model: "gpt-4o-mini", api_key: "", base_url: "" },
    chat: { system_prompt: "", max_tokens: 1000, top_k: 5 },
    crawler: { rate_limit: 1.0, skip_patterns: ["/login", "/admin", "/contact", "/careers"] },
    widget: {
        position: "bottom-right", color: "#1a73e8", logo: "", greeting: "Hi! How can I help you?",
        theme: "blue", company_name: "", button_shape: "circle", button_size: "medium",
        corner_radius: 16, font_family: "system", animation_speed: "normal",
        show_quick_replies: true, quick_replies: ["What services do you offer?", "Contact information", "Pricing", "FAQ"],
        show_emoji_picker: true, show_source_citations: true, typing_animation: "dots",
        avatar_style: "icon", unread_count: true, auto_open_delay: 0, status: "online",
        show_timestamps: false, minimize_to_icon: false, show_admin_button: true, customCSS: ""
    },
    logging: { level: "INFO" }
};

// ── Initialization ──────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    buildProgressDots();
    loadSystemInfo();
    updateCloudModels();
});

function buildProgressDots() {
    const container = document.getElementById("progressSteps");
    const labels = ["System", "Mode", "Server", "AI Model", "Chat", "Crawler", "Widget", "Deploy", "Snippet", "Install"];
    container.innerHTML = labels.map((label, i) => 
        `<div class="progress-step-dot ${i === 0 ? 'active' : ''}" id="dot${i + 1}">${i + 1}</div>`
    ).join("");
}

// ── System Info ─────────────────────────────────────────────────────

async function loadSystemInfo() {
    try {
        const resp = await fetch("/api/system-info");
        const info = await resp.json();
        const grid = document.getElementById("systemInfo");
        
        grid.innerHTML = `
            <div class="info-item">
                <div class="label">Python Version</div>
                <div class="value">${info.python_version}</div>
            </div>
            <div class="info-item">
                <div class="label">Operating System</div>
                <div class="value">${info.os.name} ${info.os.version}</div>
            </div>
            <div class="info-item">
                <div class="label">Architecture</div>
                <div class="value">${info.os.architecture}</div>
            </div>
            <div class="info-item">
                <div class="label">Ollama Installed</div>
                <div class="value">${info.ollama.installed ? "✓ Yes" : "✗ No"}</div>
            </div>
            <div class="info-item">
                <div class="label">Ollama Running</div>
                <div class="value">${info.ollama_running.running ? "✓ Yes" : "✗ No"}</div>
            </div>
            <div class="info-item">
                <div class="label">GPU</div>
                <div class="value">${info.gpu.available ? info.gpu.type : "None detected"}</div>
            </div>
            <div class="info-item">
                <div class="label">Dependencies</div>
                <div class="value">${info.dependencies.missing.length === 0 ? "✓ All installed" : `${info.dependencies.missing.length} missing`}</div>
            </div>
            <div class="info-item">
                <div class="label">Recommended Port</div>
                <div class="value">${info.default_port}</div>
            </div>
        `;

        const warnings = document.getElementById("systemWarnings");
        let warningsHtml = "";
        if (!info.ollama.installed) {
            warningsHtml += `<div class="warning-item">⚠️ Ollama is not installed. For local mode, install from https://ollama.ai</div>`;
        }
        if (!info.ollama_running.running && info.ollama.installed) {
            warningsHtml += `<div class="warning-item">⚠️ Ollama is installed but not running. Start with: ollama serve</div>`;
        }
        if (info.dependencies.missing.length > 0) {
            warningsHtml += `<div class="warning-item error">⚠️ Missing dependencies: ${info.dependencies.missing.join(", ")}</div>`;
        }
        if (info.ports && info.ports["8000_in_use"]) {
            warningsHtml += `<div class="warning-item">⚠️ Port 8000 is already in use</div>`;
        }
        warnings.innerHTML = warningsHtml;
    } catch (e) {
        console.error("Failed to load system info:", e);
    }
}

// ── Step Navigation ─────────────────────────────────────────────────

function nextStep() {
    if (currentStep < totalSteps) {
        if (currentStep === 4) collectStep4Data();
        if (currentStep === 9) generateSnippets();
        if (currentStep === 10) generateConfigPreview();
        currentStep++;
        updateUI();
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateUI();
    }
}

function updateUI() {
    document.querySelectorAll(".wizard-step").forEach(el => el.classList.remove("active"));
    document.getElementById(`step${currentStep}`).classList.add("active");
    
    for (let i = 1; i <= totalSteps; i++) {
        const dot = document.getElementById(`dot${i}`);
        dot.classList.remove("active", "completed");
        if (i === currentStep) dot.classList.add("active");
        else if (i < currentStep) dot.classList.add("completed");
    }
    
    const pct = ((currentStep - 1) / (totalSteps - 1)) * 100;
    document.getElementById("progressFill").style.width = pct + "%";
    document.getElementById("progressLabel").textContent = `Step ${currentStep} of ${totalSteps}`;
    
  document.getElementById("prevBtn").style.display = currentStep === 1 ? "none" : "block";
    const nextBtn = document.getElementById("nextBtn");
    nextBtn.textContent = currentStep === totalSteps ? "Finish" : "Next →";
    if (currentStep === totalSteps) {
        nextBtn.onclick = isInstalled ? nextStep : () => runInstall();
    } else {
        nextBtn.onclick = nextStep;
    }
    
    if (currentStep === totalSteps) {
        generateConfigPreview();
    }
    
    window.scrollTo(0, 0);
}

// ── Step 2: Mode Selection ──────────────────────────────────────────

function selectMode(mode) {
    wizardData.mode = mode;
    document.querySelectorAll(".mode-card").forEach(el => el.classList.remove("selected"));
    document.querySelector(`.mode-card[data-mode="${mode}"]`).classList.add("selected");
    
    document.getElementById("localConfig").style.display = mode === "cloud" ? "none" : "block";
    document.getElementById("cloudConfig").style.display = mode === "local" ? "none" : "block";
}

// ── Step 4: AI Model ────────────────────────────────────────────────

async function checkOllamaModels() {
    const url = document.getElementById("ollamaUrl").value;
    const statusEl = document.getElementById("ollamaStatus");
    statusEl.textContent = "Checking...";
    
    try {
        const resp = await fetch(`/api/ollama/models?ollama_url=${encodeURIComponent(url)}`);
        const data = await resp.json();
        
        if (data.running && data.models.length > 0) {
            statusEl.innerHTML = `<span style="color:var(--success)">✓ Connected! Found ${data.models.length} model(s)</span>`;
            const select = document.getElementById("ollamaModel");
            select.innerHTML = "";
            data.models.forEach(m => {
                const opt = document.createElement("option");
                opt.value = m.name;
                opt.textContent = `${m.name} (${formatSize(m.size)})`;
                select.appendChild(opt);
            });
            const optCustom = document.createElement("option");
            optCustom.value = "custom";
            optCustom.textContent = "Custom model...";
            select.appendChild(optCustom);
        } else {
            statusEl.innerHTML = `<span style="color:var(--warning)">No models found. Pull one with: ollama pull qwen2.5:3b</span>`;
        }
    } catch (e) {
        statusEl.innerHTML = `<span style="color:var(--error)">Cannot connect: ${e.message}</span>`;
    }
}

function updateCloudModels() {
    const provider = document.getElementById("cloudProvider").value;
    const select = document.getElementById("cloudModel");
    const azureGroup = document.getElementById("azureBaseUrlGroup");
    
    azureGroup.style.display = provider === "azure" ? "block" : "none";
    
    const models = {
        openai: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        anthropic: ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        azure: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        google: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        groq: ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
        together: ["meta-llama/Llama-3-8b-chat-hf", "meta-llama/Llama-3-70b-chat-hf"]
    };
    
    select.innerHTML = "";
    (models[provider] || []).forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        select.appendChild(opt);
    });
}

function togglePassword(id) {
    const input = document.getElementById(id);
    input.type = input.type === "password" ? "text" : "password";
}

function formatSize(bytes) {
    if (!bytes) return "N/A";
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(1)} GB`;
}

function collectStep4Data() {
    const mode = wizardData.mode;
    
    if (mode !== "cloud") {
        wizardData.ollama.url = document.getElementById("ollamaUrl").value;
        const modelVal = document.getElementById("ollamaModel").value;
        wizardData.ollama.model = modelVal === "custom" ? document.getElementById("customModel").value : modelVal;
        wizardData.ollama.embedding_model = document.getElementById("embeddingModel").value;
    }
    
    if (mode === "cloud" || mode === "hybrid") {
        wizardData.cloud.provider = document.getElementById("cloudProvider").value;
        wizardData.cloud.model = document.getElementById("cloudModel").value;
        wizardData.cloud.api_key = document.getElementById("cloudApiKey").value;
        wizardData.cloud.base_url = document.getElementById("cloudBaseUrl").value;
    }
}

// ── Step 5-7: Collect Data ──────────────────────────────────────────

function collectStep5Data() {
    wizardData.chat.system_prompt = document.getElementById("systemPrompt").value;
    wizardData.chat.max_tokens = parseInt(document.getElementById("maxTokens").value);
    wizardData.chat.top_k = parseInt(document.getElementById("topK").value);
}

function collectStep6Data() {
    wizardData.crawler.rate_limit = parseFloat(document.getElementById("rateLimit").value);
    wizardData.crawler.skip_patterns = document.getElementById("skipPatterns").value.split(",").map(s => s.trim()).filter(s => s);
}

function collectStep7Data() {
    wizardData.widget.company_name = document.getElementById("widgetCompanyName").value;
    wizardData.widget.greeting = document.getElementById("widgetGreeting").value;
    wizardData.widget.color = document.getElementById("widgetColor").value;
    wizardData.widget.position = document.getElementById("widgetPosition").value;
    wizardData.widget.logo = document.getElementById("widgetLogo").value;
    wizardData.widget.quick_replies = document.getElementById("quickReplies").value.split(",").map(s => s.trim()).filter(s => s);
}

// Show/hide custom model input when step 4 is shown
const _origUpdateUI = updateUI;
updateUI = function() {
    _origUpdateUI();
    if (currentStep === 4) {
        const customGroup = document.getElementById("customModelGroup");
        if (customGroup) {
            const modelSelect = document.getElementById("ollamaModel");
            customGroup.style.display = modelSelect && modelSelect.value === "custom" ? "block" : "none";
        }
    }
};

// Override nextStep to collect data
nextStep = function() {
    if (currentStep < totalSteps) {
        if (currentStep === 3) {
            wizardData.server.host = document.getElementById("serverHost").value;
            wizardData.server.port = parseInt(document.getElementById("serverPort").value);
            wizardData.server.username = document.getElementById("serverUsername").value;
            wizardData.server.password = document.getElementById("serverPassword").value;
        }
        if (currentStep === 4) collectStep4Data();
        if (currentStep === 5) collectStep5Data();
        if (currentStep === 6) collectStep6Data();
        if (currentStep === 7) collectStep7Data();
        if (currentStep === 9) generateSnippets();
        if (currentStep === 10) generateConfigPreview();
        currentStep++;
        updateUI();
    }
};

// ── Step 9: Snippets ────────────────────────────────────────────────

async function generateSnippets() {
    const apiBase = document.getElementById("apiBase").value;
    const format = document.getElementById("snippetFormat").value;
    const pageTitle = document.getElementById("pageTitle").value;
    
    try {
        const resp = await fetch("/api/snippets/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_base: apiBase, widget_config: wizardData.widget, page_title: pageTitle })
        });
        const data = await resp.json();
        const output = document.getElementById("snippetOutput");
        output.textContent = data.snippets[format] || "No snippets available";
    } catch (e) {
        document.getElementById("snippetOutput").textContent = `Error: ${e.message}`;
    }
}

function updateSnippets() {
    generateSnippets();
}

function copySnippet() {
    const text = document.getElementById("snippetOutput").textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector(".code-output .btn-small");
        btn.textContent = "✓ Copied!";
        setTimeout(() => btn.textContent = "Copy to Clipboard", 2000);
    });
}

// ── Step 10: Config Preview & Install ───────────────────────────────

async function generateConfigPreview() {
    collectStep3Data();
    collectStep4Data();
    collectStep5Data();
    collectStep6Data();
    collectStep7Data();
    
    wizardData.project_dir = "";
    
    const previewEl = document.getElementById("configPreview");
    previewEl.textContent = "Loading configuration...";
    
    try {
        const resp = await fetch("/api/config/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config: wizardData })
        });
        const data = await resp.json();
        previewEl.textContent = data.yaml || "No configuration generated";
    } catch (e) {
        previewEl.textContent = `Error loading config: ${e.message}`;
        console.error("Config preview error:", e);
    }
}

function collectStep3Data() {
    wizardData.server.host = document.getElementById("serverHost").value;
    wizardData.server.port = parseInt(document.getElementById("serverPort").value);
    wizardData.server.username = document.getElementById("serverUsername").value;
    wizardData.server.password = document.getElementById("serverPassword").value;
}

async function runInstall() {
    const btn = document.getElementById("installBtn");
    const logs = document.getElementById("installLogs");
    const logContent = document.getElementById("installLogContent");
    
    btn.disabled = true;
    btn.textContent = "Installing...";
    logs.style.display = "block";
    
    collectStep3Data();
    collectStep4Data();
    collectStep5Data();
    collectStep6Data();
    collectStep7Data();
    
    const projectDir = "";
    const startServer = document.getElementById("startServer").checked;
    
    try {
        const resp = await fetch("/api/install", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config: wizardData, project_dir: projectDir, start_server: startServer })
        });
        const data = await resp.json();
        
        let log = "";
        log += `✓ Config saved to: ${data.config_path}\n`;
        data.install_messages.forEach(msg => { log += `  ${msg}\n`; });
        data.deploy_files.forEach(f => { log += `  Generated: ${f}\n`; });
        if (data.server_started) { log += `  Server is starting...\n`; }
        log += `\n✓ Installation complete!`;
        
        logContent.textContent = log;
        btn.textContent = "✓ Installed";
        btn.style.background = "var(--success)";
        isInstalled = true;
    } catch (e) {
        logContent.textContent = `Error: ${e.message}`;
        btn.textContent = "Install Failed";
        btn.style.background = "var(--error)";
    }
}
