const app = {
    state: {
        theme: localStorage.getItem('theme') || 'light',
        extractedText: { recruiter: '', seeker: '' }
    },

    init() {
        this.applyTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
        
        if (window.pdfjsLib) {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }

        document.querySelectorAll('textarea').forEach(el => {
            el.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    if (el.id === 'jd-input') this.searchCandidates();
                    else if (el.id === 'resume-input') this.searchJobs();
                }
            });
        });
    },

    switchView(name) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById(`${name}-view`).classList.add('active');
        window.scrollTo(0, 0);
    },

    toggleTheme() {
        this.state.theme = this.state.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.state.theme);
        this.applyTheme();
    },

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.state.theme);
        const icon = document.querySelector('#theme-toggle i');
        icon.className = this.state.theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    },

    async handleFileUpload(event, role) {
        const file = event.target.files[0];
        if (!file) return;

        const statusId = `${role}-status`;
        const chipContainer = `${role}-file-status`;
        const textArea = document.getElementById(role === 'recruiter' ? 'jd-input' : 'resume-input');

        this.updateStatus(statusId, "PROCESSING_SOURCE_FILE...");
        
        try {
            const text = file.type === "application/pdf" ? await this.readPdf(file) : await file.text();
            if (!text || text.trim().length === 0) throw new Error("EMPTY_TEXT");

            this.state.extractedText[role] = text;
            textArea.value = "";
            textArea.placeholder = "SOURCE_READY. PROCEED_TO_MAPPING.";
            
            document.getElementById(chipContainer).innerHTML = `
                <div class="file-chip">
                    <i class="fa-solid fa-file-invoice"></i> ${file.name.toUpperCase()}
                </div>`;
            
            this.updateStatus(statusId, "READY_FOR_EXECUTION.");
        } catch (e) { 
            this.updateStatus(statusId, "SOURCE_ERROR.");
            alert("Failed to read file."); 
        } finally { 
            event.target.value = ''; 
        }
    },

    async readPdf(file) {
        const pdf = await pdfjsLib.getDocument({ data: await file.arrayBuffer() }).promise;
        let text = "";
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            text += content.items.map(s => s.str).join(" ") + "\n";
        }
        return text;
    },

    async searchCandidates() {
        const q = document.getElementById('jd-input').value || this.state.extractedText.recruiter;
        if (!q.trim()) return;
        const btn = document.getElementById('btn-recruiter-search');
        this.setLoading(btn, true, 'recruiter-status', "QUERYING_ENGINE...");
        try {
            const res = await fetch('/api/recruiter/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'recruiter');
            this.updateStatus('recruiter-status', "MAPPING_COMPLETE.");
        } catch (e) { this.updateStatus('recruiter-status', "ENGINE_FAILURE."); }
        finally { this.setLoading(btn, false); }
    },

    async searchJobs() {
        const q = document.getElementById('resume-input').value || this.state.extractedText.seeker;
        if (!q.trim()) return;
        const btn = document.getElementById('btn-seeker-search');
        this.setLoading(btn, true, 'seeker-status', "QUERYING_ENGINE...");
        try {
            const res = await fetch('/api/seeker/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'seeker');
            this.updateStatus('seeker-status', "MAPPING_COMPLETE.");
        } catch (e) { this.updateStatus('seeker-status', "ENGINE_FAILURE."); }
        finally { this.setLoading(btn, false); }
    },

    renderResults(results, type) {
        const container = document.getElementById(`${type}-results`);
        container.innerHTML = '';
        
        results.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-card';
            const score = Math.round(res.score * 100);
            const analysis = this.parseAnalysis(res.llm_analysis);
            
            const meta = res.metadata;
            const title = type === 'recruiter' ? (meta.name || "CANDIDATE") : (meta.job_title + " @ " + meta.company);
            const sub = type === 'recruiter' ? (meta.email || "CONFIDENTIAL") : (meta.location || "REMOTE");

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <h3 style="font-weight: 800; letter-spacing: -0.02em; font-size: 1.1rem;">${title.toUpperCase()}</h3>
                        <p style="color: var(--muted); font-size: 0.75rem; font-family: 'Geist Mono', monospace; margin-top: 0.2rem;">${sub}</p>
                    </div>
                    <div style="text-align: right;">
                        <div class="popover-trigger">
                            <div class="match-score">${score}%</div>
                            <div class="popover-content">
                                <div class="popover-header">
                                    <h3>MATCH_ANALYSIS</h3>
                                    <span class="match-score" style="font-size: 1rem;">${score}%</span>
                                </div>
                                ${this.renderProgressBar("Skills", analysis.skills)}
                                ${this.renderProgressBar("Experience", analysis.exp)}
                                ${this.renderProgressBar("Education", analysis.edu)}
                                
                                <div class="missing-alert">
                                    <strong>Missing_Requirements</strong>
                                    <p>${analysis.missing}</p>
                                </div>
                            </div>
                        </div>
                        <details style="display: inline-block;">
                            <summary class="icon-toggle" title="View Source"><i class="fa-solid fa-file-lines"></i></summary>
                            <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 85%; max-width: 700px; max-height: 80vh; overflow-y: auto; background: var(--bg); border: 1px solid var(--fg); padding: 2.5rem; z-index: 2000; box-shadow: 0 0 0 1000px rgba(0,0,0,0.7); font-size: 0.85rem; color: var(--muted); white-space: pre-wrap; font-family: 'Geist Mono', monospace; text-align: left;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;">
                                    <strong style="color: var(--fg)">RAW_DATA_PREVIEW</strong>
                                    <span style="cursor: pointer; color: var(--fg); font-weight: 800;" onclick="this.parentElement.parentElement.parentElement.removeAttribute('open')">[ CLOSE_X ]</span>
                                </div>
                                ${res.content}
                            </div>
                        </details>
                    </div>
                </div>
                <div class="ai-box">
                    <h4>AI_SUMMARY</h4>
                    <div style="font-size: 0.85rem; line-height: 1.5;">${analysis.summary}</div>
                </div>
            `;
            container.appendChild(card);
        });
    },

    renderProgressBar(label, value) {
        return `
            <div class="progress-group">
                <div class="progress-label">
                    <span>${label}</span>
                    <span>${value}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${value}%"></div>
                </div>
            </div>
        `;
    },

    parseAnalysis(text) {
        const defaults = { skills: 0, exp: 0, edu: 0, missing: "None detected", summary: text || "Processing..." };
        if (!text || text.includes('OFFLINE')) return defaults;

        const lines = text.split('\n');
        const getValue = (key) => lines.find(l => l.includes(key))?.split(':')[1]?.trim() || "";
        
        return {
            skills: parseInt(getValue('SKILLS_SCORE')) || 0,
            exp: parseInt(getValue('EXP_SCORE')) || 0,
            edu: parseInt(getValue('EDU_SCORE')) || 0,
            missing: getValue('MISSING') || "No major gaps",
            summary: getValue('SUMMARY') || "Analysis complete."
        };
    },

    setLoading(btn, isLoading, statusId, text) {
        if (isLoading) {
            btn.dataset.originalText = btn.innerText;
            btn.innerHTML = `<span class="loading-dots">MAPPING</span>`;
            btn.disabled = true;
            this.updateStatus(statusId, text);
        } else {
            btn.innerText = btn.dataset.originalText;
            btn.disabled = false;
        }
    },

    updateStatus(id, text) {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    },

    clearSearch(role) {
        const textArea = document.getElementById(role === 'recruiter' ? 'jd-input' : 'resume-input');
        textArea.value = '';
        this.state.extractedText[role] = '';
        document.getElementById(`${role}-results`).innerHTML = '';
        document.getElementById(`${role}-file-status`).innerHTML = '';
        document.getElementById(`${role}-status`).innerText = 'STATE_CLEARED.';
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
