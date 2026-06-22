from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('cv-match/', views.cv_match, name='cv_match'),
    path('search/', views.live_search, name='live_search'),
    path('about/', views.about, name='about'),
]