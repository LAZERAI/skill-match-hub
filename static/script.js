const app = {
    state: {
        theme: localStorage.getItem('theme') || 'light'
    },

    init() {
        this.applyTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
        
        // Add Ctrl + Enter listener to textareas
        document.querySelectorAll('textarea').forEach(el => {
            el.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    if (el.id === 'jd-input') this.searchCandidates();
                    else if (el.id === 'resume-input') this.searchJobs();
                }
            });
        });
    },

    switchView(viewName) {
        document.querySelectorAll('.view').forEach(el => {
            el.classList.remove('active');
            setTimeout(() => { if (!el.classList.contains('active')) el.classList.add('hidden'); }, 300);
        });
        const target = document.getElementById(`${viewName}-view`);
        target.classList.remove('hidden');
        setTimeout(() => target.classList.add('active'), 10);
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
        this.showLoading(true, "Extracting text...");
        try {
            const text = file.type === "application/pdf" ? await this.readPdf(file) : await file.text();
            document.getElementById(targetId).value = text;
        } catch (e) { alert("Error reading file."); }
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
        if (!q.trim()) return alert("Enter JD first.");
        this.showLoading(true);
        try {
            const res = await fetch('/api/recruiter/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'recruiter');
        } catch (e) { alert("Search failed."); }
        finally { this.showLoading(false); }
    },

    async searchJobs() {
        const q = document.getElementById('resume-input').value;
        if (!q.trim()) return alert("Enter resume first.");
        this.showLoading(true);
        try {
            const res = await fetch('/api/seeker/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: q })
            });
            const data = await res.json();
            this.renderResults(data, 'seeker');
        } catch (e) { alert("Search failed."); }
        finally { this.showLoading(false); }
    },

    renderResults(results, type) {
        const container = document.getElementById(`${type}-results`);
        container.innerHTML = '';
        
        results.forEach((res, i) => {
            const card = document.createElement('div');
            card.className = 'result-item';
            const score = Math.round(res.score * 100);
            
            // Handle LLM analysis display (Graceful error handling)
            let analysisHtml = '';
            if (res.llm_analysis) {
                if (res.llm_analysis.includes('401') || res.llm_analysis.includes('Invalid API Key')) {
                    analysisHtml = `
                        <div class="analysis-card">
                            <div class="ai-offline"><i class="fa-solid fa-circle-exclamation"></i> AI Analysis currently offline</div>
                        </div>`;
                } else {
                    analysisHtml = `
                        <div class="analysis-card">
                            <p style="font-weight: 700; margin-bottom: 0.5rem; font-size: 0.8rem; text-transform: uppercase; color: var(--primary);">
                                <i class="fa-solid fa-sparkles"></i> AI Insights
                            </p>
                            <div style="font-size: 0.95rem;">${res.llm_analysis.replace(/\n/g, '<br>')}</div>
                        </div>`;
                }
            }

            const meta = res.metadata;
            const title = type === 'recruiter' ? (meta.name || "Candidate") : (meta.job_title + " @ " + meta.company);
            const subtitle = type === 'recruiter' ? (meta.email || "Confidential Profile") : (meta.location || "Remote");

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="font-weight: 800; font-size: 1.2rem;">${title}</h3>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">${subtitle}</p>
                    </div>
                    <span class="score-tag">${score}% Match</span>
                </div>
                <div style="margin-top: 1rem; color: var(--text-muted); font-size: 0.9rem; max-height: 100px; overflow: hidden; position: relative;">
                    ${res.content}
                    <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 30px; background: linear-gradient(transparent, var(--glass));"></div>
                </div>
                ${analysisHtml}
            `;
            container.appendChild(card);
        });
    },

    clearSearch(role) {
        if (role === 'recruiter') {
            document.getElementById('jd-input').value = '';
            document.getElementById('recruiter-results').innerHTML = '';
        } else {
            document.getElementById('resume-input').value = '';
            document.getElementById('seeker-results').innerHTML = '';
        }
    },

    showLoading(isLoading, text = "Processing...") {
        const overlay = document.getElementById('loading-overlay');
        overlay.querySelector('p').innerText = text;
        overlay.className = isLoading ? '' : 'hidden';
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
