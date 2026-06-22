import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def call_claude(prompt: str, max_tokens: int = 1000) -> str:
    """Send a prompt to Claude and return the response text."""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        return ""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return ""


def generate_market_summary(jobs: list[dict]) -> str:
    """
    Send job data to Claude and get a market intelligence summary.
    """
    if not jobs:
        return "No job data available."

    # Build a condensed view of jobs for Claude
    job_lines = []
    for job in jobs[:100]:  # send max 100 jobs to stay within token limits
        line = f"- {job.get('title', '')} at {job.get('company', '')} | {job.get('location', '')} | salary: {job.get('salary_min', 'N/A')} - {job.get('salary_max', 'N/A')}"
        job_lines.append(line)

    jobs_text = "\n".join(job_lines)

    prompt = f"""You are a UK job market analyst. Analyse these {len(jobs)} UK job postings and provide a concise market intelligence summary.

Job listings:
{jobs_text}

Provide a structured analysis with these sections:
1. MARKET OVERVIEW (2-3 sentences on overall hiring activity)
2. TOP SKILLS IN DEMAND (list the 8 most mentioned technical skills)
3. HIRING HOTSPOTS (top 5 locations by job count)
4. SALARY INSIGHTS (typical ranges for different role levels)
5. NOTABLE TRENDS (2-3 interesting patterns you notice)

IMPORTANT FORMATTING RULES:
- Do NOT use markdown tables
- Do NOT use | characters
- Use plain numbered or bulleted lists only
- Keep each section concise
- No horizontal rules between sections

Be specific and data-driven. Focus on Python, automation, mechanical engineering, and German-speaking roles."""

    return call_claude(prompt, max_tokens=1500)


def extract_skills_from_jobs(jobs: list[dict]) -> dict:
    """
    Ask Claude to extract and count skills from job descriptions.
    Returns a dict of skill -> count.
    """
    if not jobs:
        return {}

    # Combine descriptions
    descriptions = []
    for job in jobs[:50]:
        desc = job.get("description", "")
        if desc:
            descriptions.append(desc[:300])  # first 300 chars per job

    combined = "\n---\n".join(descriptions)

    prompt = f"""Extract the most frequently mentioned technical skills from these UK job descriptions.

Job descriptions:
{combined}

Return ONLY a JSON object with skill names as keys and frequency count as values.
Focus on: programming languages, frameworks, tools, platforms, methodologies.
Include only skills mentioned 2+ times.
Example format: {{"Python": 45, "Docker": 23, "AWS": 18}}
Return only the JSON, nothing else."""

    response = call_claude(prompt, max_tokens=500)

    try:
        # Clean response and parse JSON
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response)
    except Exception as e:
        logger.error(f"Failed to parse skills JSON: {e}")
        return {}


def score_cv_against_job(cv_text: str, job: dict) -> dict:
    """
    Score a CV against a specific job. Returns score and missing skills.
    """
    prompt = f"""You are a UK recruitment expert. Score this CV against the job description.

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', '')}
JOB DESCRIPTION: {job.get('description', '')[:500]}

CV:
{cv_text[:1000]}

Return ONLY a JSON object with this exact format:
{{
    "score": 75,
    "matching_skills": ["Python", "Django"],
    "missing_skills": ["Docker", "AWS"],
    "recommendation": "Strong match. Consider highlighting your Docker experience."
}}
Return only the JSON, nothing else."""

    response = call_claude(prompt, max_tokens=400)

    try:
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response)
    except Exception as e:
        logger.error(f"Failed to parse CV match JSON: {e}")
        return {"score": 0, "matching_skills": [], "missing_skills": [], "recommendation": "Analysis failed."}
