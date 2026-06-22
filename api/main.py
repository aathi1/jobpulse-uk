import json
import logging
import os

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from pipeline.database import engine
from pipeline.models import Base, Job, Insight

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="JobPulse UK", version="1.0.0")

# ── Admin API Key Protection ───────────────────────────────────────────────────

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

def verify_admin(x_api_key: str = Header(None)):
    """Protect AI endpoints — only admin can trigger Claude calls."""
    if not x_api_key or x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized — admin key required")

# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "JobPulse is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ── Pipeline ───────────────────────────────────────────────────────────────────

@app.post("/pipeline/run")
def run_pipeline():
    """Trigger the ETL pipeline as a Celery background task."""
    from workers.tasks import run_pipeline as celery_pipeline
    task = celery_pipeline.delay()
    return {
        "status": "Pipeline task queued",
        "task_id": task.id,
    }

@app.get("/pipeline/status/{task_id}")
def pipeline_status(task_id: str):
    """Check the status of a running pipeline task."""
    from workers.tasks import app as celery_app
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None,
    }

# ── Jobs ───────────────────────────────────────────────────────────────────────

@app.get("/jobs")
def get_jobs(limit: int = 50, source: str = None):
    """Return jobs from the database."""
    with Session(engine) as session:
        query = session.query(Job)
        if source:
            query = query.filter(Job.source == source)
        jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        return [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "source": j.source,
                "url": j.url,
                "date_posted": j.date_posted,
            }
            for j in jobs
        ]

@app.get("/jobs/count")
def jobs_count():
    """Return total job count by source."""
    with Session(engine) as session:
        total = session.query(Job).count()
        reed = session.query(Job).filter(Job.source == "reed").count()
        adzuna = session.query(Job).filter(Job.source == "adzuna").count()
        return {"total": total, "reed": reed, "adzuna": adzuna}

@app.get("/jobs/search")
def live_search(keyword: str, limit: int = 25):
    """Live search — calls Reed + Adzuna APIs directly for any keyword."""
    from pipeline.fetch import search_reed, search_adzuna, with_retry
    from pipeline.clean import clean_jobs

    all_jobs = []
    reed_jobs = with_retry(search_reed, keyword, limit) or []
    all_jobs.extend(reed_jobs)
    adzuna_jobs = with_retry(search_adzuna, keyword, limit) or []
    all_jobs.extend(adzuna_jobs)
    cleaned = clean_jobs(all_jobs)

    return {
        "keyword": keyword,
        "total": len(cleaned),
        "results": cleaned
    }

# ── AI — Protected Endpoints ───────────────────────────────────────────────────

@app.post("/ai/market-summary")
def run_market_summary(admin=Depends(verify_admin)):
    """Generate AI market summary — admin only."""
    from ai.analyser import generate_market_summary

    with Session(engine) as session:
        jobs = session.query(Job).order_by(Job.created_at.desc()).limit(100).all()
        job_dicts = [
            {
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "description": j.description,
            }
            for j in jobs
        ]

    summary = generate_market_summary(job_dicts)
    if not summary:
        return {"error": "AI analysis failed"}

    with Session(engine) as session:
        insight = Insight(insight_type="market_summary", content=summary)
        session.add(insight)
        session.commit()

    return {"status": "done", "summary": summary}


@app.post("/ai/extract-skills")
def run_skill_extraction(admin=Depends(verify_admin)):
    """Extract top skills from job descriptions — admin only."""
    from ai.analyser import extract_skills_from_jobs

    with Session(engine) as session:
        jobs = session.query(Job).order_by(Job.created_at.desc()).limit(50).all()
        job_dicts = [{"description": j.description} for j in jobs]

    skills = extract_skills_from_jobs(job_dicts)
    if not skills:
        return {"error": "Skill extraction failed"}

    sorted_skills = dict(sorted(skills.items(), key=lambda x: x[1], reverse=True))

    with Session(engine) as session:
        insight = Insight(
            insight_type="skill_trends",
            content=json.dumps(sorted_skills)
        )
        session.add(insight)
        session.commit()

    return {"status": "done", "skills": sorted_skills}


@app.post("/ai/cv-match")
def cv_match(cv_text: str, limit: int = 10, admin=Depends(verify_admin)):
    """Score CV against top jobs — admin only."""
    from ai.analyser import score_cv_against_job

    with Session(engine) as session:
        jobs = session.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
        job_dicts = [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "description": j.description,
            }
            for j in jobs
        ]

    results = []
    for job in job_dicts:
        score = score_cv_against_job(cv_text, job)
        score["job_id"] = job["id"]
        score["title"] = job["title"]
        score["company"] = job["company"]
        results.append(score)

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"results": results}


@app.get("/ai/latest-summary")
def latest_summary():
    """Get the most recent market summary — public read only."""
    with Session(engine) as session:
        insight = (
            session.query(Insight)
            .filter(Insight.insight_type == "market_summary")
            .order_by(Insight.created_at.desc())
            .first()
        )
        if not insight:
            return {"summary": "No analysis run yet."}
        return {"summary": insight.content, "generated_at": str(insight.created_at)}