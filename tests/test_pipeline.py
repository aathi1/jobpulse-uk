import pytest
from pipeline.clean import clean_job, clean_jobs, clean_text, clean_salary, clean_location


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_raw_job():
    """A realistic raw job dict as it comes from Reed API."""
    return {
        "job_id": "reed_123",
        "title": "  Python Developer  ",
        "company": "<b>Tech Corp</b>",
        "location": "City of London",
        "salary_min": "40000.0",
        "salary_max": "55000.0",
        "description": "<p>We need Python skills</p>",
        "url": "https://reed.co.uk/jobs/123",
        "source": "reed",
        "date_posted": "2026-06-21",
    }


# ── clean_text ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("input,expected", [
    ("<p>Hello <b>World</b></p>", "Hello World"),
    ("Python   Developer",        "Python Developer"),
    ("",                          ""),
    (None,                        ""),
])
def test_clean_text(input, expected):
    assert clean_text(input) == expected


# ── clean_salary ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("input,expected", [
    (45000,       45000),
    ("45000.0",   45000),
    (None,        None),
    ("invalid",   None),
])
def test_clean_salary(input, expected):
    assert clean_salary(input) == expected


# ── clean_location ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("input,expected", [
    ("City of London",  "London"),
    ("Greater London",  "London"),
    ("",                "UK"),
    ("Manchester",      "Manchester"),
])
def test_clean_location(input, expected):
    assert clean_location(input) == expected


# ── clean_job ─────────────────────────────────────────────────────────────────

def test_clean_job_strips_html(sample_raw_job):
    result = clean_job(sample_raw_job)
    assert result["company"] == "Tech Corp"
    assert result["description"] == "We need Python skills"

def test_clean_job_normalises_salary(sample_raw_job):
    result = clean_job(sample_raw_job)
    assert result["salary_min"] == 40000
    assert result["salary_max"] == 55000

def test_clean_job_normalises_location(sample_raw_job):
    result = clean_job(sample_raw_job)
    assert result["location"] == "London"

def test_clean_job_strips_title_whitespace(sample_raw_job):
    result = clean_job(sample_raw_job)
    assert result["title"] == "Python Developer"


# ── clean_jobs ────────────────────────────────────────────────────────────────

def test_clean_jobs_skips_missing_title():
    jobs = [
        {"job_id": "reed_1", "title": "", "source": "reed"},
        {"job_id": "reed_2", "title": "Python Dev", "source": "reed"},
    ]
    result = clean_jobs(jobs)
    assert len(result) == 1
    assert result[0]["title"] == "Python Dev"

def test_clean_jobs_skips_missing_job_id():
    jobs = [
        {"job_id": "",       "title": "Python Dev",  "source": "reed"},
        {"job_id": "reed_2", "title": "Django Dev",  "source": "reed"},
    ]
    result = clean_jobs(jobs)
    assert len(result) == 1

def test_clean_jobs_returns_all_valid():
    jobs = [
        {"job_id": "reed_1", "title": "Python Dev",  "source": "reed"},
        {"job_id": "reed_2", "title": "Django Dev",  "source": "reed"},
        {"job_id": "reed_3", "title": "Flask Dev",   "source": "reed"},
    ]
    result = clean_jobs(jobs)
    assert len(result) == 3