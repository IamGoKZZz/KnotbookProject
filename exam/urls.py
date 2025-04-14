from django.contrib import admin
from django.urls import path,include
# from knotebook import views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('exam/<str:title>/', views.exam, name='exam'),
    # path('exam/<str:title>/performance/', views.student_performance, name='student_performance'),
    path('mcqperformance/', views.overall_mcq_performance, name='overall_mcq_performance'),
    path("essay/", include("essay.urls")),
    path('scorecard/<str:exam_title>/', views.scorecard, name='scorecard_page_exam'),
    path('mcq-test-analysis/', views.mcq_test_analysis, name='mcq_test_analysis'),
]
