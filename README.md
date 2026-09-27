# 🚀 RepoSense AI — Developer Onboarding & Code Quality Intelligence

> Built during the **IBM Bob 2.0 Challenge on Lablab.ai** using the **IBM Bob IDE**.

---

## 📌 Problem Statement
Joining a new engineering team or inheriting a legacy codebase is overwhelming:
- Developers spend **days deciphering architecture**, folder hierarchies, and dependencies.
- Manual code reviews frequently miss **silent anti-patterns**, hardcoded secrets, and missing error handlers.
- Junior engineers lack clear, actionable **"Good First Issues"** and setup checklists to start contributing confidently.

---

## 💡 Solution: What is RepoSense AI?
**RepoSense AI** is an intelligent developer onboarding and code health audit dashboard. By analyzing a local repository path in seconds, it provides:
1. **Architecture & Ecosystem Breakdown:** Visualizes code distribution, language percentages, and file counts using interactive Plotly charts.
2. **Static Code Quality & Security Audit:** Detects hardcoded credentials, bare `except` blocks, TODO/FIXME debt, and missing essential files (README, Dockerfile, requirements).
3. **Automated Onboarding Roadmap:** Generates an actionable first-day checklist and targeted starter tasks for newly onboarded developers.

---

## 🛠️ Built With IBM Bob 2.0
This project was designed, scaffolded, and refactored using the **IBM Bob IDE**:
- Bob AI was used to architect the static code analyzer (`analyzer.py`) and develop the modular Streamlit interface (`app.py`).
- **Proof of Work:** All session logs, token metrics, and Task Session Summaries are documented inside the [`bob_sessions/`](./bob_sessions/) directory as required by the hackathon submission guidelines.

---

## 💻 Tech Stack
- **AI / IDE:** IBM Bob 2.0 (`ibm-coding-challenge-uat`)
- **Backend & Logic:** Python 3.10+, AST & Static Analysis
- **Frontend / Dashboard:** Streamlit
- **Data & Visualization:** Pandas, Plotly Express

---

## ⚡ Quick Start Guide

### 1. Clone the Repository
```bash
git clone [https://github.com/](https://github.com/)<YOUR_GITHUB_USERNAME>/reposense-ai.git
cd reposense-ai
