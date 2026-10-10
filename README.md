# 🎬 Livik Jobs — Cinema-Grade Job Portal

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Anime.js](https://img.shields.io/badge/Anime.js-3.2.2-FF4B4B?style=for-the-badge&logo=javascript&logoColor=white)](https://animejs.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Livik Jobs** is a full-featured, multi-tenant employment platform engineered with Django and elevated by an "Absolute Cinema" visual experience. Featuring custom **Anime.js 3D physics engines**, interactive **Bento Grid** command hubs, seamless **Dark/Light Mode synchronization**, and dedicated portal ecosystems for both Job Candidates and Enterprise Employers.

---

## 🌟 Key Highlights & Visual Features

### 🎥 Absolute Cinema 3D Engine
* **Interactive 3D Tilt**: Mouse-reactive perspective cards with natural spring snapback physics.
* **Ambient Floating Field**: Floating kinetic particles and zero-gravity floating badges.
* **Specular Glare Tracking**: Radial lighting highlights that follow cursor velocity in real time.
* **HUD Rolling Counters**: Smooth numerical easing for portal statistics and metric rollups.
* **Cyber Mesh Perspective**: Deep retro-futuristic perspective grid background.

### 🌓 Unified Dark Mode Ecosystem
* **Zero-Flicker Bootstrap**: Instant DOM layout theme rendering before CSS execution.
* **Cross-App Sync**: Synchronized persistence via `localStorage` and cookies spanning Candidate, Employer, and Dashboard spaces.
* **Cinema Contrast Tokens**: Custom-crafted glassmorphism surfaces, neon cyan/amber accents, and crisp readability across dark and light states.

### 🍱 Bento Grid Architecture
* High-density, asymmetrical Bento layouts on both Candidate & Employer command hubs.
* Live-updating activity feeds, skill badges, salary benchmarks, and application velocity cards.

---

## 🏗️ System Architecture

The application is structured into modular Django apps:

| App | Description | Key Routes |
| :--- | :--- | :--- |
| **`site1`** | Candidate Public Discovery Portal | `/`, `/index/`, `/about/`, `/jobs/` |
| **`site2`** | Employer Enterprise Portal | `/site2/`, `/site2/emp_jobs/`, `/site2/pricing/` |
| **`dashb1`** | Candidate Operations Dashboard | `/dashb1/`, `/dashb1/profile/`, `/dashb1/applications/` |
| **`dashb2`** | Employer Hiring Pipeline Command | `/dashb2/`, `/dashb2/post_job/`, `/dashb2/applicants/` |
| **`account`** | Central Authentication & Session Control | `/account/login/`, `/account/register/`, `/account/logout/` |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10+ (Recommended Python 3.12 / 3.13)
* Git

### 2. Clone the Repository
```bash
git clone https://github.com/Patel-Trupt28/livik-jobs.git
cd livik-jobs
```

### 3. Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Apply Migrations & Initialize
```bash
cd job_site
python manage.py migrate
```

### 6. Start Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
* **Candidate Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Employer Portal**: [http://127.0.0.1:8000/site2/](http://127.0.0.1:8000/site2/)

---

## 🧪 Testing & User Acceptance Testing (UAT)
This codebase includes comprehensive User Acceptance Testing covering:
- Authentication & role-based routing (Employer vs. Candidate)
- Dark mode cookie & `localStorage` persistence
- Anime.js asset availability & 3D script initialization
- Job posting, search filtering, and application submission flows
- Navigation route integrity across all 4 sub-applications

**Current UAT Score:** `37 / 37 Passed (100%)`

---

## 📁 Project Structure

```text
livik-jobs/
├── .gitignore
├── requirements.txt
├── README.md
└── job_site/
    ├── manage.py
    ├── job_site/          # Core Django project settings & URLs
    ├── account/           # Authentication models & views
    ├── site1/             # Candidate frontend templates, static & views
    │   └── static/
    │       ├── css/cinema-ui.css
    │       └── js/cinema-effects.js, cinema-darkmode.js, anime.min.js
    ├── site2/             # Employer frontend templates, static & views
    ├── dashb1/            # Candidate dashboard
    └── dashb2/            # Employer hiring dashboard
```

---

## 👤 Author
* **GitHub**: [@Patel-Trupt28](https://github.com/Patel-Trupt28)

---

## 📄 License
This project is licensed under the MIT License - feel free to use and modify for personal or commercial projects.

