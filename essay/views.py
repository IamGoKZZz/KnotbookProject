import os
import re
import json
import PyPDF2
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from .models import *
from sentence_transformers import SentenceTransformer, util
from knotebook.models import student_table
from django.contrib import messages
from django.db.models import Max  

# Load FLAN-T5 Model
MODEL_NAME = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Load Sentence Transformer Model for Semantic Score Calculation
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploads")

def upload_pdf(request):
    """Handle PDF upload and trigger question generation."""
    if request.method == "POST" and request.FILES.get("pdf"):
        pdf_file = request.FILES["pdf"]
        start_page = int(request.POST["start_page"])
        num_questions = int(request.POST["num_questions"])
        exam_title = request.POST.get("exam_title")

        fs = FileSystemStorage(location=UPLOAD_DIR)
        filename = fs.save(pdf_file.name, pdf_file)
        pdf_path = os.path.join(UPLOAD_DIR, filename)

        text, total_pages = extract_text_from_pdf(pdf_path, start_page)
        if not text:
            return render(request, "upload_essay.html", {"error": "Invalid start page or empty PDF."})

        text_chunks = split_text_into_sentences(text, max_chunks=num_questions)
        generated_qa = generate_questions_and_answers(text_chunks, num_questions)

        # Store in session for verification
        request.session["generated_qa"] = generated_qa  
        request.session["pdf_path"] = pdf_path
        request.session["start_page"] = start_page
        request.session["exam_title"] = exam_title

        return redirect("verify_questions")

    # Fetch available tests
    #exam_titles = QuestionAnswer.objects.values_list("exam_title", flat=True).distinct()
    return render(request, "upload_essay.html")

def verify_page(request):
    """Display generated questions for verification."""
    generated_qa = request.session.get('generated_qa', [])
    return render(request, "verify.html", {"generated_qa": generated_qa})

def finalize_questions(request):
    """Save verified questions and redirect to results."""
    if request.method == "POST":
        selected_qa = request.POST.getlist("qa[]")
        exam_title = request.session.get("exam_title", "Untitled Exam")

        for qa in selected_qa:
            question, answer = qa.split("|||")
            question = question.strip()
            answer = answer.strip()

            # Compute semantic similarity score
            encoded_question = semantic_model.encode(question, convert_to_tensor=True)
            encoded_answer = semantic_model.encode(answer, convert_to_tensor=True)
            semantic_score = util.pytorch_cos_sim(encoded_question, encoded_answer).item()

            # Save question and answer in database
            QuestionBank.objects.create(
                exam_title=exam_title,
                question=question,
                correct_answer=answer,
                correct_answer_score=semantic_score,  # Store similarity score
            )

        return redirect("upload_pdf")

    return redirect("verify_questions")





def delete_question(request):
    """Delete a specific question-answer pair from session."""
    if request.method == "POST":
        data = json.loads(request.body)
        question_to_delete = data.get("question")
        answer_to_delete = data.get("answer")

        generated_qa = request.session.get("generated_qa", [])
        updated_qa = [qa for qa in generated_qa if not (qa[0] == question_to_delete and qa[1] == answer_to_delete)]

        request.session["generated_qa"] = updated_qa

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})

def regenerate_questions(request):
    """Regenerate additional questions dynamically while preventing duplicates."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            num_to_generate = int(data["num_questions"])
            start_page = int(data["start_page"])

            pdf_path = request.session.get("pdf_path")
            existing_qa = request.session.get("generated_qa", [])

            text, _ = extract_text_from_pdf(pdf_path, start_page)
            text_chunks = split_text_into_sentences(text, max_chunks=num_to_generate)
            new_generated_qa = generate_questions_and_answers(text_chunks, num_to_generate)

            # Ensure no duplicate questions are added
            new_generated_qa = [qa for qa in new_generated_qa if qa not in existing_qa]
            request.session["generated_qa"] += new_generated_qa  

            return JsonResponse({"success": True, "questions": [{"question": q, "answer": a} for q, a in new_generated_qa]})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

def extract_text_from_pdf(pdf_path, start_page=0):
    """Extract text from PDF starting from a given page."""
    text = []
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)

        if start_page >= total_pages:
            return None, total_pages

        for i in range(start_page, total_pages):
            extracted = reader.pages[i].extract_text()
            if extracted:
                text.append(clean_text(extracted.strip()))

    return "\n".join(text), total_pages

def clean_text(text):
    """Clean extracted text to remove unwanted metadata."""
    text = re.sub(r'\b(?:doi|journal|volume|issue|pages|author)\b.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[\w.-]+?@\w+?\.\w+?\b', '', text)  # Remove emails
    text = re.sub(r'\d+', '', text)  # Remove numbers
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_text_into_sentences(text, min_sentences=7, max_chunks=10):
    """Split text into meaningful chunks."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    chunk = []

    for sentence in sentences:
        chunk.append(sentence)
        if len(chunk) >= min_sentences:
            chunks.append(" ".join(chunk))
            chunk = []

    if chunk:
        chunks.append(" ".join(chunk))

    return chunks[:max_chunks]

def clean_answer(answer):
    """Limit the answer to 4 sentences and remove repetition."""
    sentences = re.split(r'(?<=[.!?])\s+', answer)
    unique_sentences = []
    for sentence in sentences:
        if sentence not in unique_sentences:
            unique_sentences.append(sentence)
        if len(unique_sentences) == 4:
            break
    return " ".join(unique_sentences)

def generate_questions_and_answers(text_chunks, num_questions):
    """Generate questions and answers using FLAN-T5 model."""
    text_chunks = text_chunks[:num_questions]

    inputs = [f"Generate a subjective question from the following text:\n{text}" for text in text_chunks]
    tokenized_inputs = tokenizer(inputs, return_tensors="pt", padding=True, truncation=True, max_length=512)

    questions = model.generate(**tokenized_inputs, max_length=100, num_beams=3, temperature=0.7)
    decoded_questions = [tokenizer.decode(q, skip_special_tokens=True).strip() for q in questions]

    answer_inputs = [f"Generate a detailed answer with at most 3 sentences for the question: '{q}' based on:\n{text}" for q, text in zip(decoded_questions, text_chunks)]
    tokenized_answers = tokenizer(answer_inputs, return_tensors="pt", padding=True, truncation=True, max_length=512)

    answers = model.generate(**tokenized_answers, max_length=300, min_length=50, num_beams=3, temperature=0.7)
    decoded_answers = [clean_answer(tokenizer.decode(a, skip_special_tokens=True).strip()) for a in answers]
    return list(zip(decoded_questions, decoded_answers))

def compute_similarity(answer1, answer2):
    """Compute semantic similarity score between two answers."""
    # Encode answers
    encoded_answer1 = semantic_model.encode([answer1], convert_to_tensor=True)  # Keep input as a list
    encoded_answer2 = semantic_model.encode([answer2], convert_to_tensor=True)

    # Compute cosine similarity
    similarity = util.pytorch_cos_sim(encoded_answer1, encoded_answer2).item()

    # Convert to percentage
    return round(similarity * 100, 2)

# def take_test(request, exam_title):
#     """Fetches questions related to the selected exam title."""
#     questions = QuestionAnswer.objects.filter(exam_title=exam_title)
#     return render(request, "result.html", {"questions": questions, "exam_title": exam_title})
def result_page(request, exam_title):
    """Handle exam submission, compute scores, and redirect to scorecard."""
    if "sid" not in request.session:  # Check if student is logged in
        return HttpResponse("Student not logged in", status=401)  # Redirect to login if session expired

    student_id = request.session["sid"]  # Get student ID from session
    student = student_table.objects.get(id=student_id)  # Fetch student using ID

    # Check if student has already taken the test
    if StudentResponse.objects.filter(student=student, exam_title=exam_title).exists():
        messages.error(request, "You have already attempted this test.")
        return redirect("scorecard_page", exam_title=exam_title)  # Redirect to scorecard

    if request.method == "POST":
        questions_answers = QuestionBank.objects.filter(exam_title=exam_title)
        total_questions = questions_answers.count()
        correct_answers = 0

        for qa in questions_answers:
            user_response = request.POST.get(f"response_{qa.id}", "").strip()
            semantic_score = compute_similarity(qa.correct_answer, user_response) if user_response else 0.0

            # Store user's response and score in the database
            StudentResponse.objects.create(
                student=student,  # Store student
                exam_title=exam_title,
                question=qa,  # Linking the QuestionBank object directly
                user_response=user_response,
                user_response_score=semantic_score
            )

            # Check if answer is correct (>= 90% similarity)
            if semantic_score >= 90.0:
                correct_answers += 1

        return redirect("scorecard_page", exam_title=exam_title)  # Redirect to scorecard page

    # If GET request, show exam questions
    questions_answers = QuestionBank.objects.filter(exam_title=exam_title)
    return render(request, "result.html", {"questions_answers": questions_answers, "exam_title": exam_title})

def scorecard_page(request, exam_title):
    """Display the scorecard after exam submission and store TGPA."""
    if "sid" not in request.session:  # Check if student is logged in
        return redirect("login")  # Redirect to login if session expired

    student_id = request.session["sid"]  # Get student ID from session
    student = student_table.objects.get(id=student_id)  # Fetch student using ID

    # Retrieve student responses for the given test
    user_answers = StudentResponse.objects.filter(student=student, exam_title=exam_title)
    total_questions = user_answers.count()
    total_marks = total_questions * 3  # Each question carries 3 marks

    marks_obtained = 0

    for qa in user_answers:
        if qa.user_response_score >= 95:
            qa.marks_obtained = 3  # Full marks if relevance > 95%
        else:
            qa.marks_obtained = round((qa.user_response_score / 100) * 3, 2)  # Proportional marks

        marks_obtained += qa.marks_obtained
        qa.save()  # ✅ Store individual marks

    # Compute Overall Score Percentage
    overall_score_percentage = round((marks_obtained / total_marks) * 100, 2) if total_questions > 0 else 0

    # Compute TGPA (Test Grade Points) out of 10
    tgpa = round((marks_obtained / total_marks) * 10, 2) if total_questions > 0 else 0

    # ✅ Store TGPA in the database for the specific student's test attempt
    user_answers.update(tgpa=tgpa)

    return render(request, "scorecard_essay.html", {
        "total_questions": total_questions,
        "marks_obtained": marks_obtained,
        "total_marks": total_marks,
        "overall_score_percentage": overall_score_percentage,
        "tgpa": tgpa,  # ✅ Now stored in DB
        "user_answers": user_answers,
        "exam_title": exam_title
    })

def test_performance(request):
    """ Display subjective test performance for a student """

    # Fetch student_id from session or GET parameter
    student_id = request.session.get("sid") or request.GET.get("student_id")

    if not student_id:
        return render(request, "test_performance.html", {"error": "Student ID is missing."})

    # Fetch student details
    student = student_table.objects.filter(id=student_id).first()
    if not student:
        return render(request, "test_performance.html", {"error": "Student not found."})

    # Get latest TGPA per exam_title
    responses = (
        StudentResponse.objects.filter(student_id=student_id)
        .values("exam_title")
        .annotate(latest_tgpa=Max("tgpa"), latest_created=Max("created_at"))
        .order_by("latest_created")
    )

    if not responses:
        return render(request, "test_performance.html", {
            "student_name": student.name,
            "error": "No performance data found."
        })

    exam_titles = [response["exam_title"] for response in responses]  
    tgpa_scores = [response["latest_tgpa"] for response in responses]  

    return render(request, "test_performance.html", {
        "student_name": student.name,
        "exam_titles": json.dumps(exam_titles),
        "tgpa_scores": json.dumps(tgpa_scores),
    })

def subjective_test_analysis(request):
    # Get list of students who attended tests
    students = StudentResponse.objects.values_list('student', flat=True).distinct()
    
    student_data = []
    for student_id in students:
        student = student_table.objects.filter(id=student_id).first()  # Fetch student details
        attended_tests = StudentResponse.objects.filter(student=student_id).values_list('exam_title', flat=True).distinct()

        if student:  # Ensure student exists
            student_data.append({
                'student_id': student_id,
                'student_name': student.name,  # Get student name
                'attended_tests': list(attended_tests),
            })

    return render(request, 'subjective_test_analysis.html', {'students': student_data})
