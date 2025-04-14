from django.db import models
from django.utils import timezone
from knotebook.models import student_table

class Question(models.Model):
    question_text = models.TextField() 
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_answer = models.TextField() 
    question_type=models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    title=models.TextField() 

class StudentExamScore(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student= models.IntegerField()
    user_answer = models.TextField()
    test_title = models.CharField(max_length=255)
    question_type = models.CharField(max_length=50)
    marks_obtained = models.IntegerField()
    total_marks = models.IntegerField()
    tgpa_exam = models.FloatField(default=0.0)
    attempted_at = models.DateTimeField(default=timezone.now)  # Stores attempt timestamp
