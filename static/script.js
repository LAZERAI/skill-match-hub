const app = {
    state: {
        theme: localStorage.getItem('theme') || 'light'
    },

    init() {
        this.applyTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
        
        // Ctrl + Enter support
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

    async handleFileUpload(event, targetId) {
        const file = event.target.files[0];
        if (!file) return;
        this.showLoading(true, "READING_LOCAL_FILESYSTEM...");
        try {
            const text = file.type === "application/pdf" ? await this.readPdf(file) : await file.text();
            document.getElementById(targetId).value = text;
        } catch (e) { alert("FILE_READ_FAILURE"); }
        finally { this.showLoading(false); event.target.value = ''; }
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
        const q = document.getElementById('jd-input').value;
        if (!q.trim()) return;
        this.showLoading(true, "EXECUTING_SEMANTIC_QUERY...");
        try {
            const res = await fetch('/api/recruiter/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'recruiter');
        } catch (e) { alert("QUERY_EXECUTION_FAILURE"); }
        finally { this.showLoading(false); }
    },

    async searchJobs() {
        const q = document.getElementById('resume-input').value;
        if (!q.trim()) return;
        this.showLoading(true, "EXECUTING_SEMANTIC_QUERY...");
        try {
            const res = await fetch('/api/seeker/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'seeker');
        } catch (e) { alert("QUERY_EXECUTION_FAILURE"); }
        finally { this.showLoading(false); }
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
                    <div class="ai-box" style="${isError ? 'opacity: 0.5; border-top-color: var(--muted);' : ''}">
                        <h4>${isError ? 'AI_ENGINE_OFFLINE' : 'AI_GENERATED_INSIGHTS'}</h4>
                        <div style="font-size: 0.9rem;">${res.llm_analysis.replace(/\n/g, '<br>')}</div>
                    </div>`;
            }

            const meta = res.metadata;
            const title = type === 'recruiter' ? (meta.name || "CANDIDATE") : (meta.job_title + " @ " + meta.company);
            const sub = type === 'recruiter' ? (meta.email || "CONFIDENTIAL") : (meta.location || "REMOTE");

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h3 style="letter-spacing: -0.02em;">${title.toUpperCase()}</h3>
                        <p style="color: var(--muted); font-size: 0.8rem; font-family: 'Geist Mono', monospace;">${sub}</p>
                    </div>
                    <div class="match-score">${score}%</div>
                </div>
                <div style="margin-top: 1.5rem; font-size: 0.85rem; color: var(--muted); line-height: 1.4;">
                    ${res.content}
                </div>
                ${analysisHtml}
            `;
            container.appendChild(card);
        });
    },

    clearSearch(role) {
        document.getElementById(role === 'recruiter' ? 'jd-input' : 'resume-input').value = '';
        document.getElementById(`${role}-results`).innerHTML = '';
    },

    showLoading(isLoading, text = "PROCESSING...") {
        const overlay = document.getElementById('loading-overlay');
        overlay.querySelector('p').innerText = text;
        overlay.className = isLoading ? '' : 'hidden';
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
