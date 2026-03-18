const app = {
    state: {
        theme: localStorage.getItem('theme') || 'light',
        extractedText: { recruiter: '', seeker: '' }
    },

    init() {
        this.applyTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
        
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

        this.updateStatus(statusId, "EXTRACTING_TEXT...");
        
        try {
            const text = file.type === "application/pdf" ? await this.readPdf(file) : await file.text();
            
            // Store text in background state
            this.state.extractedText[role] = text;
            
            // Clear textarea and show chip
            textArea.value = "";
            textArea.placeholder = "TEXT_EXTRACTED_FROM_FILE. READY_TO_MAP.";
            
            document.getElementById(chipContainer).innerHTML = `
                <div class="file-chip">
                    <i class="fa-solid fa-file-code"></i> ${file.name}
                </div>`;
            
            this.updateStatus(statusId, "EXTRACTION_COMPLETE.");
        } catch (e) { 
            this.updateStatus(statusId, "EXTRACTION_ERROR.");
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
        if (!q.trim()) return alert("No input provided.");
        
        const btn = document.getElementById('btn-recruiter-search');
        const status = 'recruiter-status';
        
        this.setLoading(btn, true, status, "QUERYING_ENGINE...");
        try {
            const res = await fetch('/api/recruiter/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'recruiter');
            this.updateStatus(status, "MAPPING_SUCCESSFUL.");
        } catch (e) { 
            this.updateStatus(status, "QUERY_FAILURE.");
        } finally { 
            this.setLoading(btn, false); 
        }
    },

    async searchJobs() {
        const q = document.getElementById('resume-input').value || this.state.extractedText.seeker;
        if (!q.trim()) return alert("No input provided.");

        const btn = document.getElementById('btn-seeker-search');
        const status = 'seeker-status';

        this.setLoading(btn, true, status, "QUERYING_ENGINE...");
        try {
            const res = await fetch('/api/seeker/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'seeker');
            this.updateStatus(status, "MAPPING_SUCCESSFUL.");
        } catch (e) { 
            this.updateStatus(status, "QUERY_FAILURE.");
        } finally { 
            this.setLoading(btn, false); 
        }
    },

    renderResults(results, type) {
        const container = document.getElementById(`${type}-results`);
        container.innerHTML = '';
        
        results.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-card';
            const score = Math.round(res.score * 100);
            
            let analysisHtml = '';
            if (res.llm_analysis) {
                const isError = res.llm_analysis.includes('_ERROR') || res.llm_analysis.includes('_OFFLINE');
                analysisHtml = `
                    <div class="ai-box" style="${isError ? 'opacity: 0.5;' : ''}">
                        <h4>${isError ? 'AI_OFFLINE' : 'AI_INSIGHTS'}</h4>
                        <div style="font-size: 0.85rem; line-height: 1.5;">${res.llm_analysis.replace(/\n/g, '<br>')}</div>
                    </div>`;
            }

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
                        <div class="match-score">${score}%</div>
                        <details style="display: inline-block;">
                            <summary class="icon-toggle" title="View Source"><i class="fa-solid fa-file-lines"></i></summary>
                            <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; max-width: 600px; max-height: 70vh; overflow-y: auto; background: var(--bg); border: 1px solid var(--fg); padding: 2rem; z-index: 2000; box-shadow: 0 0 0 1000px rgba(0,0,0,0.5); font-size: 0.85rem; color: var(--muted); white-space: pre-wrap; font-family: 'Geist Mono', monospace;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;">
                                    <strong style="color: var(--fg)">RAW_CONTEXT_SOURCE</strong>
                                    <span style="cursor: pointer; color: var(--fg)" onclick="this.parentElement.parentElement.parentElement.removeAttribute('open')">CLOSE [X]</span>
                                </div>
                                ${res.content}
                            </div>
                        </details>
                    </div>
                </div>
                ${analysisHtml}
            `;
            container.appendChild(card);
        });
    },

    setLoading(btn, isLoading, statusId, text) {
        if (isLoading) {
            btn.dataset.originalText = btn.innerText;
            btn.innerHTML = `<span class="loading-dots">PROCESSING</span>`;
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
        textArea.placeholder = role === 'recruiter' ? 'INPUT_JOB_DESCRIPTION // CTRL+ENTER_TO_PROCESS' : 'INPUT_RESUME_TEXT // CTRL+ENTER_TO_PROCESS';
        this.state.extractedText[role] = '';
        document.getElementById(`${role}-results`).innerHTML = '';
        document.getElementById(`${role}-file-status`).innerHTML = '';
        document.getElementById(`${role}-status`).innerText = 'RESET_COMPLETE.';
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
