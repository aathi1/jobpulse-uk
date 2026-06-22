import re
import logging

logger = logging.getLogger(__name__)


def clean_date(date_str: str) -> str:
    """Normalise date to YYYY-MM-DD."""
    if not date_str:
        return ""
    # Strip time portion from ISO format
    return date_str[:10]
    
def clean_text(text: str) -> str:
    """Remove HTML tags and extra whitespace from text."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_salary(value) -> int | None:
    """Normalise salary to integer or None."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def clean_location(location: str) -> str:
    """Normalise location string."""
    if not location:
        return "UK"
    location = location.strip()
    # Normalise common variations
    replacements = {
        "City of London": "London",
        "Greater London": "London",
        "London, UK": "London",
        "England, UK": "UK",
        "England": "UK",
    }
    return replacements.get(location, location)


def clean_title(title: str) -> str:
    """Clean job title."""
    if not title:
        return ""
    # Remove extra whitespace
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def clean_job(job: dict) -> dict:
    """Clean a single job dict — runs between fetch and store."""
    return {
        "job_id": job.get("job_id", ""),
        "title": clean_title(job.get("title", "")),
        "company": clean_text(job.get("company", "")),
        "location": clean_location(job.get("location", "")),
        "salary_min": clean_salary(job.get("salary_min")),
        "salary_max": clean_salary(job.get("salary_max")),
        "description": clean_text(job.get("description", "")),
        "url": job.get("url", ""),
        "source": job.get("source", ""),
        "date_posted": clean_date(job.get("date_posted", "")),
    }


def clean_jobs(jobs: list[dict]) -> list[dict]:
    """Clean a list of jobs. Skips any job missing job_id or title."""
    cleaned = []
    skipped = 0

    for job in jobs:
        # Skip jobs with no ID or title — useless records
        if not job.get("job_id") or not job.get("title"):
            skipped += 1
            continue
        cleaned.append(clean_job(job))

    logger.info(f"Cleaned: {len(cleaned)} jobs | Skipped invalid: {skipped}")
    return cleaned
