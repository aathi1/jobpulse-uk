import os
import logging
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Celery app ────────────────────────────────────────────────────────────────

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "jobpulse",
    broker=REDIS_URL,    # Redis receives tasks here
    backend=REDIS_URL,   # Redis stores results here
)

app.conf.timezone = "UTC"

# ── Schedule ──────────────────────────────────────────────────────────────────

app.conf.beat_schedule = {
    "fetch-jobs-every-6-hours": {
        "task": "workers.tasks.run_pipeline",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "ai-analysis-daily": {
        "task": "workers.tasks.run_ai_analysis",
        "schedule": crontab(minute=0, hour=8),
    },
}

# ── Tasks ─────────────────────────────────────────────────────────────────────

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_pipeline(self):
    """
    Full ETL pipeline as a Celery task.
    Runs automatically every 6 hours via Celery Beat.
    Retries up to 3 times if it fails.
    """
    try:
        from pipeline.fetch import fetch_all_jobs
        from pipeline.clean import clean_jobs
        from pipeline.store import save_jobs

        logger.info("Celery: Pipeline task started")

        jobs = fetch_all_jobs()
        jobs = clean_jobs(jobs)
        result = save_jobs(jobs)

        logger.info(f"Celery: Pipeline complete — {result}")
        return result

    except Exception as exc:
        logger.error(f"Celery: Pipeline failed — {exc}")
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_ai_analysis(self):
    """
    Run AI market summary daily.
    Scheduled separately from the pipeline.
    """
    try:
        from ai.analyser import generate_market_summary, extract_skills_from_jobs
        from pipeline.models import Insight
        from pipeline.database import engine
        from sqlalchemy.orm import Session

        logger.info("Celery: AI analysis started")

        with Session(engine) as session:
            from pipeline.models import Job
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

        if summary:
            with Session(engine) as session:
                insight = Insight(
                    insight_type="market_summary",
                    content=summary
                )
                session.add(insight)
                session.commit()
            logger.info("Celery: AI analysis complete")

        return {"status": "done"}

    except Exception as exc:
        logger.error(f"Celery: AI analysis failed — {exc}")
        raise self.retry(exc=exc)
