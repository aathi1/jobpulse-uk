from sqlalchemy.orm import Session
from pipeline.models import Job
from pipeline.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_jobs(jobs: list[dict]):
    """Save a list of jobs to PostgreSQL, skipping duplicates."""
    saved = 0
    skipped = 0

    with Session(engine) as session:
        for job_data in jobs:
            # Check if job already exists
            exists = session.query(Job).filter_by(
                job_id=job_data["job_id"]
            ).first()

            if exists:
                skipped += 1
                continue

            job = Job(
                job_id=job_data["job_id"],
                title=job_data["title"],
                company=job_data.get("company"),
                location=job_data.get("location"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                description=job_data.get("description"),
                url=job_data.get("url"),
                source=job_data.get("source"),
                date_posted=job_data.get("date_posted"),
            )
            session.add(job)
            saved += 1

        session.commit()

    logger.info(f"Saved: {saved} jobs | Skipped duplicates: {skipped}")
    return {"saved": saved, "skipped": skipped}
