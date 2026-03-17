const app = {
    state: {
        currentView: 'landing',
        theme: localStorage.getItem('theme') || 'light'
    },

    init() {
        this.applyTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
    },

    switchView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(el => {
            el.classList.remove('active');
            setTimeout(() => {
                if (!el.classList.contains('active')) el.classList.add('hidden');
            }, 300); // Match CSS transition
        });

        // Show target view
        const target = document.getElementById(`${viewName}-view`);
        target.classList.remove('hidden');
        
        // Small delay to allow display:block to apply before opacity transition
        setTimeout(() => {
            target.classList.add('active');
        }, 10);

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
        if (this.state.theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    },

    async searchCandidates() {
        const query = document.getElementById('jd-input').value;
        if (!query.trim()) return alert("Please enter a job description.");

        this.showLoading(true);
        try {
            const response = await fetch('/api/recruiter/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 5 })
            });
            
            if (!response.ok) throw new Error('Search failed');
            
            const results = await response.json();
            this.renderRecruiterResults(results);
        } catch (err) {
            console.error(err);
            alert("Error fetching candidates. Please try again.");
        } finally {
            this.showLoading(false);
        }
    },

    async searchJobs() {
        const query = document.getElementById('resume-input').value;
        if (!query.trim()) return alert("Please enter your resume text.");

        this.showLoading(true);
        try {
            const response = await fetch('/api/seeker/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 5 })
            });
            
            if (!response.ok) throw new Error('Search failed');
            
            const results = await response.json();
            this.renderSeekerResults(results);
        } catch (err) {
            console.error(err);
            alert("Error fetching jobs. Please try again.");
        } finally {
            this.showLoading(false);
        }
    },

    renderRecruiterResults(results) {
        const container = document.getElementById('recruiter-results');
        container.innerHTML = '';
        
        if (results.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:var(--text-secondary)">No matching candidates found.</p>';
            return;
        }

        results.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-card';
            
            // Extract metadata safely
            const name = res.metadata.name || "Unknown Candidate";
            const email = res.metadata.email || "No email";
            const skills = res.metadata.skills ? res.metadata.skills.join(', ') : "Not listed";
            const exp = res.metadata.total_experience_years || 0;

            let llmHtml = '';
            if (res.llm_analysis) {
                // Convert newlines to breaks for basic formatting
                const analysisText = res.llm_analysis.replace(/\n/g, '<br>');
                llmHtml = `
                    <div class="llm-analysis">
                        <h4><i class="fa-solid fa-robot"></i> AI Analysis</h4>
                        <p>${analysisText}</p>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="result-header">
                    <h3>${name}</h3>
                    <span class="score-badge">Match: ${(res.score * 100).toFixed(0)}%</span>
                </div>
                <p><strong><i class="fa-solid fa-envelope"></i></strong> ${email}</p>
                <p><strong><i class="fa-solid fa-briefcase"></i> Exp:</strong> ${exp} years</p>
                <p><strong><i class="fa-solid fa-code"></i> Skills:</strong> ${skills}</p>
                <p style="margin-top:0.5rem; color:var(--text-secondary)">${res.content}</p>
                ${llmHtml}
            `;
            container.appendChild(card);
        });
    },

    renderSeekerResults(results) {
        const container = document.getElementById('seeker-results');
        container.innerHTML = '';

        if (results.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:var(--text-secondary)">No matching jobs found.</p>';
            return;
        }

        results.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-card';
            
            const title = res.metadata.job_title || "Unknown Role";
            const company = res.metadata.company || "Unknown Company";
            const location = res.metadata.location || "Remote/Unknown";

            let llmHtml = '';
            if (res.llm_analysis) {
                 const analysisText = res.llm_analysis.replace(/\n/g, '<br>');
                llmHtml = `
                    <div class="llm-analysis">
                        <h4><i class="fa-solid fa-lightbulb"></i> Career Advice</h4>
                        <p>${analysisText}</p>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="result-header">
                    <h3>${title}</h3>
                    <span class="score-badge">Match: ${(res.score * 100).toFixed(0)}%</span>
                </div>
                <p><strong><i class="fa-solid fa-building"></i></strong> ${company}</p>
                <p><strong><i class="fa-solid fa-map-marker-alt"></i></strong> ${location}</p>
                <p style="margin-top:0.5rem; color:var(--text-secondary)">${res.content}</p>
                ${llmHtml}
            `;
            container.appendChild(card);
        });
    },

    showLoading(isLoading) {
        const overlay = document.getElementById('loading-overlay');
        if (isLoading) overlay.classList.remove('hidden');
        else overlay.classList.add('hidden');
    }
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => app.init());
