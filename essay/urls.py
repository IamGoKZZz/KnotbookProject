from django.urls import path
from .views import upload_pdf, result_page, verify_page, finalize_questions, regenerate_questions, delete_question, scorecard_page,test_performance,subjective_test_analysis

urlpatterns = [
    path("", upload_pdf, name="upload_pdf"),
    path("results/<str:exam_title>/", result_page, name="result_page"),
    path("verify/", verify_page, name="verify_questions"),
    path("finalize/", finalize_questions, name="finalize_questions"),
    path("regenerate_questions/", regenerate_questions, name="regenerate_questions"),
    path("delete-question/", delete_question, name="delete_question"),
    path("results/<str:exam_title>/scorecard/", scorecard_page, name="scorecard_page"),
    # path("test/<str:exam_title>/", take_test, name="take_test"),
    path("performance/", test_performance, name="test_performance"),
    path('subjective-test-analysis/', subjective_test_analysis, name='subjective_test_analysis'),
    
]
