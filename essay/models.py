from django.db import models
from knotebook.models import student_table  # Import student model

# Table to store exam questions and correct answers
class QuestionBank(models.Model):
    exam_title = models.CharField(max_length=255)  # Title of the exam
    question = models.TextField()  # Exam question
    correct_answer = models.TextField()  # Correct answer
    correct_answer_score = models.FloatField(default=0.0)  # Score for correct answer

    def __str__(self):
        return f"{self.exam_title} - {self.question[:50]}..."  # Show part of the question

# Table to store student responses and scores
class StudentResponse(models.Model):
    student = models.ForeignKey(student_table, on_delete=models.CASCADE)  # Link to student
    exam_title = models.CharField(max_length=255)  # Link to exam title
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE)  # Link to question
    user_response = models.TextField(blank=True, null=True)  # Student's answer
    
    user_response_score = models.FloatField(default=0.0)  # Score for user's response
    marks_obtained = models.FloatField(default=0.0)  # ✅ New Field: Individual marks per question
    tgpa = models.FloatField(default=0.0)  # Total grade point average for student
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when response is recorded

    def __str__(self):
        return f"{self.student.name} - {self.exam_title} - {self.question.question[:50]}..."
