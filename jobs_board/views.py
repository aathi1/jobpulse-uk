from django.shortcuts import render
from django.db.models import Count
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from .models import Job, Insight
import json, os
import requests


SPAM_COMPANIES = ['ITOL', 'IT Career Switch', 'ITOL Recruit']


def get_base_qs():
    """Base queryset excluding spam companies."""
    qs = Job.objects.all()
    for company in SPAM_COMPANIES:
        qs = qs.exclude(company__icontains=company)
    return qs


def index(request):
    # Get filter params
    source = request.GET.get('source', '')
    location = request.GET.get('location', '')
    company = request.GET.get('company', '')
    min_salary = request.GET.get('min_salary', '')
    max_salary = request.GET.get('max_salary', '')
    keyword = request.GET.get('keyword', '')

    # Base queryset — no spam
    base_qs = get_base_qs()
    jobs = base_qs.order_by('-created_at')

    # Apply filters
    if source:
        jobs = jobs.filter(source=source)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if company:
        jobs = jobs.filter(company__icontains=company)
    if keyword:
        jobs = jobs.filter(title__icontains=keyword)
    if min_salary:
        try:
            jobs = jobs.filter(salary_min__gte=int(min_salary))
        except ValueError:
            pass
    if max_salary:
        try:
            jobs = jobs.filter(salary_max__lte=int(max_salary))
        except ValueError:
            pass

    # Stats
    total_jobs = base_qs.count()
    reed_count = base_qs.filter(source='reed').count()
    adzuna_count = base_qs.filter(source='adzuna').count()
    with_salary = base_qs.filter(salary_min__isnull=False).count()
    filtered_count = jobs.count()

    # Sidebar filters
    top_locations = (
        base_qs
        .exclude(location='')
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    top_companies = (
        base_qs
        .exclude(company='')
        .values('company')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # AI summary
    latest_summary = None
    try:
        insight = (
            Insight.objects
            .filter(insight_type='market_summary')
            .order_by('-created_at')
            .first()
        )
        if insight:
            latest_summary = {
                'content': insight.content,
                'created_at': insight.created_at,
            }
    except Exception:
        pass

    # Skill trends
    skill_trends = None
    try:
        skill_insight = (
            Insight.objects
            .filter(insight_type='skill_trends')
            .order_by('-created_at')
            .first()
        )
        if skill_insight:
            skills = json.loads(skill_insight.content)
            skill_trends = list(skills.items())[:8]
    except Exception:
        pass

    context = {
        'jobs': jobs[:50],
        'total_jobs': total_jobs,
        'reed_count': reed_count,
        'adzuna_count': adzuna_count,
        'with_salary': with_salary,
        'filtered_count': filtered_count,
        'top_locations': top_locations,
        'top_companies': top_companies,
        'latest_summary': latest_summary,
        'skill_trends': skill_trends,
        'filters': {
            'source': source,
            'location': location,
            'company': company,
            'min_salary': min_salary,
            'max_salary': max_salary,
            'keyword': keyword,
        }
    }
    return render(request, 'jobs_board/index.html', context)


def job_detail(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        raise Http404("Job not found")
    return render(request, 'jobs_board/detail.html', {'job': job})


@csrf_exempt
def cv_match(request):
    if request.method == 'POST':
        cv_text = request.POST.get('cv_text', '')
        limit = request.POST.get('limit', '10')

        try:
            limit = int(limit)
            if limit < 1: limit = 1
            if limit > 50: limit = 50
        except ValueError:
            limit = 10

        if not cv_text:
            return render(request, 'jobs_board/cv_match.html', {
                'error': 'Please paste your CV text.',
                'limit': limit,
            })

        try:
            admin_key = os.getenv("ADMIN_API_KEY", "")
            response = requests.post(
                'http://api:8000/ai/cv-match',
                params={'cv_text': cv_text, 'limit': limit},
                headers={'x-api-key': admin_key},
                timeout=120
            )
            results = response.json().get('results', [])
        except Exception:
            results = []

        return render(request, 'jobs_board/cv_match.html', {
            'results': results,
            'cv_text': cv_text,
            'limit': limit,
        })

    return render(request, 'jobs_board/cv_match.html', {'limit': 10})



def live_search(request):
    """Live search — calls Reed + Adzuna APIs directly for any keyword."""
    keyword = request.GET.get('keyword', '').strip()
    results = []
    error = None
    reed_count = 0
    adzuna_count = 0

    if keyword:
        try:
            response = requests.get(
                'http://api:8000/jobs/search',
                params={'keyword': keyword, 'limit': 25},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                reed_count = sum(1 for j in results if j.get('source') == 'reed')
                adzuna_count = sum(1 for j in results if j.get('source') == 'adzuna')
            else:
                error = "Search failed. Please try again."
        except Exception as e:
            error = f"Search error: {str(e)}"

    return render(request, 'jobs_board/live_search.html', {
        'keyword': keyword,
        'results': results,
        'error': error,
        'reed_count': reed_count,
        'adzuna_count': adzuna_count,
    })


def about(request):
    return render(request, 'jobs_board/about.html', {})