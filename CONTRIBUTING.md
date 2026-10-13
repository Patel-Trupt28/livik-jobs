# Contributing to Livik Jobs

Thank you for your interest in contributing to **Livik Jobs**! 🎬

Livik Jobs is a multi-tenant Django job portal featuring an "Absolute Cinema" visual interface. We welcome bug fixes, design improvements, and feature contributions.

---

## Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/<your-username>/livik-jobs.git
cd livik-jobs
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations & System Checks
```bash
cd job_site
python manage.py migrate
python manage.py check
```

---

## Submitting Pull Requests
1. Create a descriptive feature branch: `git checkout -b feature/cool-new-ui`.
2. Keep code clean and adhere to PEP 8 standards.
3. Ensure no static file regressions in dark/light mode.
4. Submit a Pull Request targeting `main`.
