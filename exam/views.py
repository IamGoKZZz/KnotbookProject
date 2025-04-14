from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import *
from knotebook.models import student_table
import pdfplumber
import fitz  # PyMuPDF for PDF text extraction
import os
import json
import re
import random
import time
import torch
import nlpcloud
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import google.generativeai as genai
from essay.views import *
from essay.models import QuestionBank # Subjective Model
from django.urls import reverse
from statistics import mean
import time
from google.api_core.exceptions import ResourceExhausted

# Set up Gemini API
API_KEY = "AIzaSyCEeOXu5AAOvRkialuEXfiqP20_w"
genai.configure(api_key=API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-1.5-pro")
# print("Using API Key:", API_KEY)

# Load T5 model for MCQ question generation
tokenizer = AutoTokenizer.from_pretrained("potsawee/t5-large-generation-squad-QuestionAnswer", trust_remote_code=True)
model_t5 = AutoModelForSeq2SeqLM.from_pretrained("potsawee/t5-large-generation-squad-QuestionAnswer", trust_remote_code=True)

def extract_text_from_pdf(pdf_path, start_page):
    """Extracts text from a PDF file starting from a given page."""
    doc = fitz.open(pdf_path)
    text = " ".join([doc[page].get_text("text") for page in range(start_page - 1, len(doc))])
    return text.strip()

def split_text_into_chunks(text, sentences_per_chunk=4):
    """Splits text into 4-sentence chunks."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = [" ".join(sentences[i:i + sentences_per_chunk]) for i in range(0, len(sentences), sentences_per_chunk)]
    return [chunk for chunk in chunks if len(chunk.split()) > 10]  # Filter out very short chunks

def generate_distractors(question, correct_answer):
    """Generates distractors for MCQs using Gemini API without explanations."""
    prompt = f"For the given question: '{question}' and correct answer: '{correct_answer}', generate three incorrect but plausible multiple-choice answers. Only return the answers, without any explanations or additional text."
    
    try:
        response = gemini_model.generate_content(prompt)
    except ResourceExhausted:
        # Wait for a while before retrying
        time.sleep(60)  # Wait for 60 seconds
        response = gemini_model.generate_content(prompt)
    
    if not response or not response.text:
        return []
    
    distractors = response.text.strip().split("\n")
    clean_distractors = []
    for d in distractors:
        d = re.sub(r'^[\d\*\-•]+\s*', '', d).strip()
        d = re.sub(r'\(.*?\)', '', d).strip()
        if d and d.lower() != correct_answer.lower():
            clean_distractors.append(d)

    return list(dict.fromkeys(clean_distractors))[:3]  # Remove duplicates and limit to 3

def generate_mcqs(text, num_questions):
    """Generates MCQs using T5 and Gemini, processing one chunk at a time."""
    generated_questions = []
    sentence_chunks = split_text_into_chunks(text)

    for chunk in sentence_chunks[:num_questions]:  # Process only required chunks
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
        outputs = model_t5.generate(**inputs, max_length=100, num_return_sequences=1, do_sample=True, temperature=0.7)
        question_answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "?" in question_answer:
            question, correct_answer = question_answer.split("?", 1)
            question += "?"
        else:
            continue

        question, correct_answer = question.strip(), correct_answer.strip()
        distractors = generate_distractors(question, correct_answer)
        time.sleep(2)  # Add a delay to avoid hitting the API quota too quickly

        if len(distractors) == 3:
            options = [correct_answer] + distractors
            random.shuffle(options)
            option_labels = ['A', 'B', 'C', 'D']
            correct_answer_label = next(label for label, option in zip(option_labels, options) if option == correct_answer)

            generated_questions.append({
                'question_text': question,
                'option_a': options[0],
                'option_b': options[1],
                'option_c': options[2],
                'option_d': options[3],
                'correct_answer': correct_answer_label
            })

        if len(generated_questions) >= num_questions:
            break  

    return generated_questions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf', 'txt']
def index(request):
    student_id = request.session.get('sid')  # Fetch the logged-in user's ID
    
 

    # Fetch all test titles for MCQ and Subjective
    all_mcq_tests = set(Question.objects.values_list('title', flat=True))
    all_subjective_tests = set(QuestionBank.objects.values_list("exam_title", flat=True))

    # Fetch attended test titles from StudentExamScore (MCQ)
    attended_mcq_tests = set(
        StudentExamScore.objects.filter(student=student_id)
        .values_list('test_title', flat=True)
    )

    # Fetch attended test titles from StudentResponse (Subjective)
    attended_subjective_tests = set(
        StudentResponse.objects.filter(student__id=student_id)
        .values_list('exam_title', flat=True)
    )

    # Identify non-attended tests
    non_attended_mcq_tests = sorted(list(all_mcq_tests - attended_mcq_tests))
    non_attended_subjective_tests = sorted(list(all_subjective_tests - attended_subjective_tests))

    context = {
        'attended_mcq_tests': sorted(attended_mcq_tests),
        'non_attended_mcq_tests': non_attended_mcq_tests,
        'attended_subjective_tests': sorted(attended_subjective_tests),
        'non_attended_subjective_tests': non_attended_subjective_tests,
    }

    return render(request, 'examindex.html', context)

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        num_questions = int(request.POST.get('num_questions', 5))
        question_type = request.POST.get('question_type', 'mcq')  
        title = request.POST.get('title')
        start_page = int(request.POST.get('start_page', 1))  # Ensure it defaults to 1

        if question_type == "subjective":
            return redirect("/test/essay/")
        
        if allowed_file(file.name):
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            extracted_text = extract_text_from_pdf(file_path, start_page)
            questions_data = generate_mcqs(extracted_text, num_questions)

            if not questions_data:
                return HttpResponse("Error: Failed to generate questions from the uploaded file.", status=400)

            for question_data in questions_data:
                Question.objects.create(
                    question_text=question_data['question_text'],
                    option_a=question_data['option_a'],
                    option_b=question_data['option_b'],
                    option_c=question_data['option_c'],
                    option_d=question_data['option_d'],
                    correct_answer=question_data['correct_answer'],
                    question_type=question_type,
                    created_at=timezone.now(),
                    title=title
                )

            messages.success(request, "Questions have been generated successfully!")
            return redirect('/test/?success=true')  # Redirect with success flag

    return render(request, 'upload.html')
def exam(request, title):
    student_id = request.session.get('sid')
    if not student_id:
        return HttpResponse("Student not logged in", status=401)

    # Check if student has already taken the test
    if StudentExamScore.objects.filter(student=student_id, test_title=title).exists():
        messages.error(request, "You have already attempted this test.")
        return redirect("scorecard_page_exam", exam_title=title)

    if request.method == 'POST':
        user_answers = request.POST
        questions = Question.objects.filter(title=title)
        total_questions = questions.count()
        score = 0

        for question in questions:
            user_answer = user_answers.get(str(question.id), "Not Answered")
            is_correct = user_answer == question.correct_answer
            if is_correct:
                score += 1

            # Save each question's answer to the database
            StudentExamScore.objects.create(
                student=student_id,
                question=question,
                user_answer=user_answer,
                test_title=title,
                question_type=question.question_type,
                marks_obtained=1 if is_correct else 0,
                total_marks=1
            )

        # Redirect to the scorecard page
        return redirect("scorecard_page_exam", exam_title=title)

    questions = Question.objects.filter(title=title)
    return render(request, 'exam.html', {'questions': questions, 'title': title})


def scorecard(request, exam_title):
    student_id = request.session.get('sid')
    if not student_id:
        return HttpResponse("Student not logged in", status=401)

    # Retrieve all the student's answers and score details
    scores = StudentExamScore.objects.filter(student=student_id, test_title=exam_title)

    if not scores.exists():
        messages.error(request, "No previous attempt found.")
        return redirect("index")

    total_score = sum(score.marks_obtained for score in scores)
    total_questions = scores.count()
    
    # Calculate TGPA (Normalized score out of 10)
    tgpa = round((total_score / total_questions) * 10, 2) if total_questions > 0 else 0.0

    # Update TGPA in database
    scores.update(tgpa_exam=tgpa)

    # Prepare question data for display
    question_data = []
    for score in scores:
        # Fetch actual text of the chosen option
        user_answer_text = getattr(score.question, f"option_{score.user_answer.lower()}", score.user_answer)
        correct_answer_text = getattr(score.question, f"option_{score.question.correct_answer.lower()}", score.question.correct_answer)

        question_data.append({
            'question_text': score.question.question_text,
            'user_answer': user_answer_text,
            'correct_answer': correct_answer_text,
            'is_correct': score.marks_obtained == 1
        })

    return render(request, 'scorecard.html', {
        'score': total_score,
        'total_questions': total_questions,
        'tgpa': tgpa,
        'title': exam_title,
        'questions': question_data
    })

def overall_mcq_performance(request):
    """ Display overall MCQ performance and TGPA trend """
    
    # Fetch student_id from session or GET parameter
    student_id = request.session.get("sid") or request.GET.get("student_id")

    if not student_id:
        return render(request, "mcq_performance.html", {"error": "Student ID is missing."})

    # Fetch student details
    student = student_table.objects.filter(id=student_id).first()
    if not student:
        return render(request, "mcq_performance.html", {"error": "Student not found."})

    # Fetch MCQ scores for the student
    mcq_scores = StudentExamScore.objects.filter(student=student_id, question_type="MCQ").order_by("attempted_at")

    if not mcq_scores.exists():
        return render(request, "mcq_performance.html", {
            "student_name": student.name,
            "overall_labels": json.dumps([]),
            "overall_scores": json.dumps([]),
            "pie_chart_values": json.dumps([]),
            "tgpa_labels": json.dumps([]),
            "tgpa_scores": json.dumps([]),
            "average_tgpa": 0,  # Default to 0 if no scores exist
            "title": "Overall MCQ Performance"
        })

    # Extract unique test titles and sum scores per test
    overall_labels = list(dict.fromkeys(score.test_title for score in mcq_scores))
    overall_scores = [sum(score.marks_obtained for score in mcq_scores if score.test_title == test) for test in overall_labels]

    # Prepare data for pie chart
    total_score = sum(overall_scores)
    pie_chart_values = [{"label": label, "y": (score / total_score) * 100} for label, score in zip(overall_labels, overall_scores)] if total_score > 0 else []

    # Extract TGPA scores
    tgpa_data = {score.test_title: score.tgpa_exam for score in mcq_scores}
    tgpa_labels = list(tgpa_data.keys())
    tgpa_scores = list(tgpa_data.values())

    # **Calculate Average TGPA**
    average_tgpa = round(mean(tgpa_scores), 2) if tgpa_scores else 0  # Avoid division by zero

    return render(request, "mcq_performance.html", {
        "student_name": student.name,
        "overall_labels": json.dumps(overall_labels),
        "overall_scores": json.dumps(overall_scores),
        "pie_chart_values": json.dumps(pie_chart_values),
        "tgpa_labels": json.dumps(tgpa_labels),
        "tgpa_scores": json.dumps(tgpa_scores),
        "average_tgpa": average_tgpa,  # Pass average TGPA to template
        "title": "Overall MCQ Performance"
    })

def mcq_test_analysis(request):
    # Get list of students who attended tests
    students = StudentExamScore.objects.values_list('student', flat=True).distinct()
    
    student_data = []
    for student_id in students:
        student = student_table.objects.filter(id=student_id).first()  # Fetch student details
        attended_tests = StudentExamScore.objects.filter(student=student_id).values_list('test_title', flat=True).distinct()
        
        if student:  # Ensure student exists
            student_data.append({
                'student_id': student_id,
                'student_name': student.name,  # Get student name
                'attended_tests': list(attended_tests),
            })

    return render(request, 'mcq_test_analysis.html', {'students': student_data})
