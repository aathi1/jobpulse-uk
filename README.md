# ⚡ JobPulse UK

> Personal UK job market intelligence platform — built during my own job search.

## 🎯 Why I Built This

When I moved to the UK and started applying for jobs, I hit a wall — pure silence.
Hundreds of applications, no responses. I had no idea what the market actually wanted,
which skills were in demand, or whether my CV was even getting past ATS filters.

So I built JobPulse. It automatically fetches 500+ UK job postings daily, analyses them
with Claude AI, and tells me exactly what skills are missing from my CV.

**It is not just a portfolio project. I use it every day.**

## 🚀 Features

- Automated ETL Pipeline — fetches jobs from Reed and Adzuna every 6 hours via Celery Beat
- AI Market Analysis — Claude API analyses job descriptions, extracts skill trends
- CV Matcher — paste your CV, get scored against live UK jobs with missing skills
- Live Search — search any role, fetched directly from APIs in real time
- Django Dashboard — filterable job board with clickable sidebar and salary ranges
- FastAPI REST API — 11 endpoints with auto-generated Swagger docs
- pytest Suite — 15 unit tests covering all data cleaning functions
- Deduplication — job_id based dedup prevents duplicate entries in PostgreSQL

## 🛠️ Tech Stack

- Backend API: FastAPI + Uvicorn
- Dashboard: Django
- Database: PostgreSQL 15
- Task Queue: Celery + Redis
- AI Analysis: Claude API (Anthropic)
- Containerisation: Docker + Docker Compose
- CI/CD: GitHub Actions
- Cloud: AWS EC2 + RDS
- Testing: pytest
- Data: Pandas, SQLAlchemy
- Job Sources: Reed API + Adzuna API

## 🚦 Getting Started

### Prerequisites
- Docker + Docker Compose
- Reed API key (free at reed.co.uk/developers)
- Adzuna API key (free at developer.adzuna.com)
- Anthropic API key (console.anthropic.com)

### Setup

git clone https://github.com/aathi1/jobpulse-uk.git
cd jobpulse-uk
cp .env.example .env
Edit .env with your API keys
docker compose up --build

### Access

- Django Dashboard: http://localhost:8001
- FastAPI + Swagger: http://localhost:8000/docs
- Live Search: http://localhost:8001/search/
- CV Matcher: http://localhost:8001/cv-match/
- About: http://localhost:8001/about/

### Run Tests

docker compose exec api pytest tests/ -v

## 🔌 API Endpoints

- GET  /              — Health check
- GET  /health        — Health check
- POST /pipeline/run  — Trigger ETL pipeline
- GET  /pipeline/status/{id} — Check pipeline status
- GET  /jobs          — List jobs filterable
- GET  /jobs/count    — Job counts by source
- GET  /jobs/search   — Live search any keyword
- POST /ai/market-summary — Generate AI market report
- POST /ai/extract-skills — Extract skill trends
- POST /ai/cv-match   — Score CV against jobs
- GET  /ai/latest-summary — Get latest AI summary

## 🌍 Environment Variables

Copy .env.example to .env and fill in your keys.

POSTGRES_DB=jobpulse
POSTGRES_USER=jobpulse_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
REED_API_KEY=your_reed_key
ADZUNA_APP_ID=your_adzuna_id
ADZUNA_APP_KEY=your_adzuna_key
ANTHROPIC_API_KEY=your_anthropic_key

## 👨‍💻 About The Builder

Aathithyan Venkatesh — Python Developer and Mechanical Engineer

- Location: Bournemouth, UK — UK Right to Work
- LinkedIn: https://linkedin.com/in/aathi101
- GitHub: https://github.com/aathi1
- Email: aathithyan1@gmail.com

7 years of German corporate data extraction at Altrata-BoardEx plus self-taught Python
developer with two live deployed applications. Now seeking full-time Python or
automation engineering roles in the UK.

## 📄 License

MIT License — see LICENSE for details.

Job data sourced from Reed and Adzuna APIs under their standard developer terms.
AI analysis powered by Anthropic Claude API.
