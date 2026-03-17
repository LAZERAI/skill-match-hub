const app = {
    state: {
        currentView: 'landing',
        theme: localStorage.getItem('theme') || 'light',
        rawResults: [],
        blindMode: false
    },

    init() {
        this.applyTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
    },

    switchView(viewName) {
        document.querySelectorAll('.view').forEach(el => {
            el.classList.remove('active');
            setTimeout(() => { if (!el.classList.contains('active')) el.classList.add('hidden'); }, 300);
        });
        const target = document.getElementById(`${viewName}-view`);
        target.classList.remove('hidden');
        setTimeout(() => target.classList.add('active'), 10);
        this.state.currentView = viewName;
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

    toggleBlindMode() {
        this.state.blindMode = document.getElementById('blind-mode-toggle').checked;
        const container = document.getElementById('recruiter-results');
        if (this.state.blindMode) container.classList.add('blind-mode-active');
        else container.classList.remove('blind-mode-active');
    },

    filterResults() {
        const threshold = parseInt(document.getElementById('threshold-slider').value);
        document.getElementById('threshold-val').innerText = threshold;
        const sortBy = document.getElementById('sort-order').value;

        let filtered = this.state.rawResults.filter(r => (r.score * 100) >= threshold);
        
        if (sortBy === 'score') filtered.sort((a, b) => b.score - a.score);
        else if (sortBy === 'exp') filtered.sort((a, b) => (b.metadata.total_experience_years || 0) - (a.metadata.total_experience_years || 0));

        this.renderResultsToUI(filtered);
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
            this.state.rawResults = await res.json();
            document.getElementById('recruiter-controls').classList.remove('hidden');
            this.filterResults();
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
            this.renderSeekerResults(data);
        } catch (e) { alert("Search failed."); }
        finally { this.showLoading(false); }
    },

    renderResultsToUI(results) {
        const container = document.getElementById('recruiter-results');
        container.innerHTML = '';
        results.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-card';
            const score = Math.round(res.score * 100);
            const meta = res.metadata;
            
            const llmData = this.parseLLMOutput(res.llm_analysis);

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start">
                    <div>
                        <h3 class="candidate-name">${meta.name || "Candidate"}</h3>
                        <p style="font-size:0.9rem; color:var(--text-secondary)">${meta.email || ""}</p>
                    </div>
                    <div class="match-circle">
                        <svg viewBox="0 0 36 36">
                            <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                            <path class="circle-progress" stroke-dasharray="${score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        </svg>
                        <div class="match-text">${score}%</div>
                    </div>
                </div>
                <div style="margin-top:1rem">
                    <p><strong>Experience:</strong> ${meta.total_experience_years || 0} Years</p>
                    <div style="margin-top:0.5rem">
                        ${llmData.matched.map(s => `<span class="skill-tag skill-matched">${s}</span>`).join('')}
                        ${llmData.missing.map(s => `<span class="skill-tag skill-missing">${s}</span>`).join('')}
                    </div>
                </div>
                <div class="analysis-box">
                    <p style="font-size:0.9rem">${llmData.summary || res.llm_analysis}</p>
                </div>
            `;
            container.appendChild(card);
        });
    },

    renderSeekerResults(results) {
        const container = document.getElementById('seeker-results');
        container.innerHTML = '';
        results.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-card';
            const score = Math.round(res.score * 100);
            const llmData = this.parseLLMOutput(res.llm_analysis, true);

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between">
                    <h3>${res.metadata.job_title} @ ${res.metadata.company}</h3>
                    <div class="match-circle">
                         <svg viewBox="0 0 36 36">
                            <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                            <path class="circle-progress" stroke-dasharray="${score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        </svg>
                        <div class="match-text">${score}%</div>
                    </div>
                </div>
                <div class="analysis-box" style="border-left-color: var(--accent-green)">
                    <p><strong><i class="fa-solid fa-check"></i> Skills You Have:</strong> ${llmData.matched.join(', ')}</p>
                    <p style="margin-top:0.5rem"><strong><i class="fa-solid fa-lightbulb"></i> Skills to Learn:</strong> ${llmData.missing.join(', ')}</p>
                    <p style="margin-top:0.5rem; font-style:italic; color:var(--text-secondary)">${llmData.summary}</p>
                </div>
            `;
            container.appendChild(card);
        });
    },

    parseLLMOutput(text, isSeeker = false) {
        if (!text || text.includes('Error')) return { matched: [], missing: [], summary: text };
        const lines = text.split('\n');
        const getList = (prefix) => {
            const line = lines.find(l => l.toUpperCase().includes(prefix));
            if (!line) return [];
            return line.split(':')[1].replace(/[\[\]]/g, '').split(',').map(s => s.trim());
        };
        return {
            matched: getList('MATCHED SKILLS'),
            missing: getList(isSeeker ? 'SKILLS GAP' : 'MISSING SKILLS'),
            summary: lines.find(l => l.toUpperCase().includes(isSeeker ? 'ADVICE' : 'SUMMARY'))?.split(':')[1] || ""
        };
    },

    clearSearch(role) {
        if (role === 'recruiter') {
            document.getElementById('jd-input').value = '';
            document.getElementById('recruiter-results').innerHTML = '';
            document.getElementById('recruiter-controls').classList.add('hidden');
        } else {
            document.getElementById('resume-input').value = '';
            document.getElementById('seeker-results').innerHTML = '';
        }
    },

    showLoading(isLoading, text = "Analyzing with AI...") {
        const overlay = document.getElementById('loading-overlay');
        overlay.querySelector('p').innerText = text;
        overlay.className = isLoading ? '' : 'hidden';
    }
};
document.addEventListener('DOMContentLoaded', () => app.init());
