import os
import time
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REED_API_KEY   = os.getenv("REED_API_KEY")
ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

REED_SEARCH_TERMS = [
    "junior python developer",
    "python developer",
    "python automation engineer",
    "python automation developer",
    "automation engineer python",
    "data engineer python",
    "ETL developer python",
    "django developer",
    "flask developer",
    "python engineer manufacturing",
    "test automation engineer python",
    "CATIA engineer",
    "junior mechanical design engineer",
    "mechanical design engineer",
    "SolidWorks design engineer",
    "german speaking python",
    "german speaking engineer",
]

ADZUNA_SEARCH_TERMS = [
    "junior python developer",
    "python automation engineer",
    "django developer",
    "flask developer",
    "data engineer python",
    "ETL python developer",
    "CATIA design engineer",
    "junior mechanical design engineer",
    "mechanical engineer CAD",
    "german speaking python",
    "german speaking engineer",
]


def with_retry(func, *args, retries=3, delay=5, **kwargs):
    """Retry a function up to 3 times with exponential backoff."""
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Failed after {retries} attempts: {e}")
                return []


def search_reed(keyword: str, results_to_take: int = 25) -> list[dict]:
    """Fetch jobs from Reed API for a given keyword."""
    if not REED_API_KEY:
        logger.warning("REED_API_KEY not set")
        return []

    url = "https://www.reed.co.uk/api/1.0/search"
    params = {
        "keywords": keyword,
        "locationName": "United Kingdom",
        "resultsToTake": results_to_take,
        "fullTime": True,
    }

    try:
        response = requests.get(
            url,
            params=params,
            auth=(REED_API_KEY, ""),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        jobs = []

        for r in data.get("results", []):
            jobs.append({
                "job_id": f"reed_{r.get('jobId')}",
                "title": r.get("jobTitle", ""),
                "company": r.get("employerName", ""),
                "location": r.get("locationName", ""),
                "salary_min": r.get("minimumSalary"),
                "salary_max": r.get("maximumSalary"),
                "description": r.get("jobDescription", ""),
                "url": r.get("jobUrl", ""),
                "source": "reed",
                "date_posted": str(r.get("date", "")),
            })

        logger.info(f"Reed '{keyword}': {len(jobs)} jobs fetched")
        return jobs

    except Exception as e:
        logger.error(f"Reed error for '{keyword}': {e}")
        return []


def search_adzuna(keyword: str, results: int = 25) -> list[dict]:
    """Fetch jobs from Adzuna API for a given keyword."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna credentials not set")
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keyword,
        "where": "UK",
        "results_per_page": results,
        "content-type": "application/json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        jobs = []

        for r in data.get("results", []):
            jobs.append({
                "job_id": f"adzuna_{r.get('id')}",
                "title": r.get("title", ""),
                "company": r.get("company", {}).get("display_name", ""),
                "location": r.get("location", {}).get("display_name", ""),
                "salary_min": r.get("salary_min"),
                "salary_max": r.get("salary_max"),
                "description": r.get("description", ""),
                "url": r.get("redirect_url", ""),
                "source": "adzuna",
                "date_posted": str(r.get("created", "")),
            })

        logger.info(f"Adzuna '{keyword}': {len(jobs)} jobs fetched")
        return jobs

    except Exception as e:
        logger.error(f"Adzuna error for '{keyword}': {e}")
        return []


def fetch_all_jobs() -> list[dict]:
    """Fetch jobs from all sources and return combined list."""
    all_jobs = []

    logger.info(f"Starting Reed fetch — {len(REED_SEARCH_TERMS)} search terms")
    for term in REED_SEARCH_TERMS:
        jobs = with_retry(search_reed, term)
        all_jobs.extend(jobs or [])
        time.sleep(0.5)

    logger.info(f"Starting Adzuna fetch — {len(ADZUNA_SEARCH_TERMS)} search terms")
    for term in ADZUNA_SEARCH_TERMS:
        jobs = with_retry(search_adzuna, term)
        all_jobs.extend(jobs or [])
        time.sleep(0.5)

    logger.info(f"Total jobs fetched: {len(all_jobs)}")
    return all_jobs
