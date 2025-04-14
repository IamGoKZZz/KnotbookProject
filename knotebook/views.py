from pyexpat.errors import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from .models import *
from django.shortcuts import redirect
# FILE UPLOAD AND VIEW
from  django.core.files.storage import FileSystemStorage
# SESSION
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Avg, Max
from django.contrib import messages 

from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.pdfgen import canvas # type: ignore
from django.utils.timezone import now

from exam.models import StudentExamScore
from essay.models import StudentResponse
from statistics import mean

def first(request):
    return render(request,'index.html')


def login(request):
    return render(request,'login.html')

def addlogin(request):
    email=request.POST.get('email')
    password=request.POST.get('password')
    if email=='admin@gmail.com' and password=='admin':
        request.session['login_id']=email
        print("Working")
        return render(request, 'login.html', {'login_status': 'success', 'redirect_url': 'first'})
        
    
    elif hodtable.objects.filter(email=email).exists():
        userdetails = hodtable.objects.get(email=email)
        if check_password(password, userdetails.password):
            request.session['hid'] = userdetails.id
            request.session['hname'] = userdetails.name
            request.session.set_expiry(3600)
            return render(request, 'login.html', {'login_status': 'success', 'redirect_url': 'home'})
    elif teacher.objects.filter(email=email).exists():
        userdetails=teacher.objects.get(email=email)
        if check_password(password, userdetails.password):
            request.session['tid'] = userdetails.id
            request.session['tname'] = userdetails.name
            request.session.set_expiry(3600)
            return render(request, 'login.html', {'login_status': 'success', 'redirect_url': 'home'})
        
    elif student_table.objects.filter(email=email).exists():
        userdetails=student_table.objects.get(email=email)
        if check_password(password, userdetails.password):
            request.session['sid'] = userdetails.id
            request.session['sname'] = userdetails.name
            request.session.set_expiry(3600)
            return render(request, 'login.html', {'login_status': 'success', 'redirect_url': 'home'})
              # Logout after 1 hour of inactivity
    
    return render(request,'login.html', {'login_status': 'failed'})
    

def logout(request):
    session_keys=list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    return redirect(first)

def home(request):
    return render(request,'index.html')



def tech(request):
    return render(request,'staff.html')

def addteacher(request):
    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        name=request.POST.get('name')
        phone=request.POST.get('phone')
     
        experience=request.POST.get('experience')
        qualification=request.POST.get('qualification')
        department=request.POST.get('department')
        dob=request.POST.get('dob')
         # Handling file uploads for 'idproof' and 'profile_picture'
        idproof_file = request.FILES['idproof']
        profile_picture_file = request.FILES.get('profile_picture')  # Using get() to avoid errors if the field is empty

        fs = FileSystemStorage()

        # Save the idproof file
        idproof_filepath = fs.save(idproof_file.name, idproof_file)

        # Save the profile picture if uploaded
        profile_picture_filepath = None
        if profile_picture_file:
            profile_picture_filepath = fs.save(profile_picture_file.name, profile_picture_file)
        # filepath= "Testing"
        ins=teacher(name=name, email=email, phone=phone,
                    password=make_password(password), experience=experience,
                    qualification=qualification, department=department,
                    dob=dob, idproof=idproof_filepath,profile_picture=profile_picture_filepath)
        ins.save()
        
    return render(request,'index.html',{'message':"Successfully Registered"})

def hod(request):
    return render(request,'hod.html')

def addhod(request):
    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        name=request.POST.get('name')
        phone=request.POST.get('phone')
     
        experience=request.POST.get('experience')
        qualification=request.POST.get('qualification')
        department=request.POST.get('department')
        # Handling file uploads for 'idproof' and 'profile_picture'
        idproof_file = request.FILES['idproof']
        profile_picture_file = request.FILES.get('profile_picture')  # Using get() to avoid errors if the field is empty

        fs = FileSystemStorage()

        # Save the idproof file
        idproof_filepath = fs.save(idproof_file.name, idproof_file)

        # Save the profile picture if uploaded
        profile_picture_filepath = None
        if profile_picture_file:
            profile_picture_filepath = fs.save(profile_picture_file.name, profile_picture_file)

        # filepath= "Testing"
        ins=hodtable(name=name, email=email, phone=phone,
                    password=make_password(password), experience=experience,
                    qualification=qualification, department=department,
                    idproof=idproof_filepath,profile_picture=profile_picture_filepath )
        ins.save()
        
    return render(request,'index.html',{'message':"Successfully Registerd"})
    #return render(request,'hod.html')

def student(request):
    return render(request,'student.html')

def addstudent(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        dob = request.POST.get('dob')
        department = request.POST.get('department')

        # Handling file uploads for 'idproof' and 'profile_picture'
        idproof_file = request.FILES['idproof']
        profile_picture_file = request.FILES.get('profile_picture')  # Using get() to avoid errors if the field is empty

        fs = FileSystemStorage()

        # Save the idproof file
        idproof_filepath = fs.save(idproof_file.name, idproof_file)

        # Save the profile picture if uploaded
        profile_picture_filepath = None
        if profile_picture_file:
            profile_picture_filepath = fs.save(profile_picture_file.name, profile_picture_file)

        # Create and save the student record
        ins = student_table(
            name=name,
            email=email,
            phone=phone,
            password=make_password(password),
            age=age,
            dob=dob,
            department=department,
            idproof=idproof_filepath,
            status="pending",
            profile_picture=profile_picture_filepath  # Save the profile picture path if uploaded
        )
        ins.save()

    return render(request, 'student.html')

def viewstd(request):
    std=student_table.objects.all()
    return render(request,'viewstd.html',{'result':std})

def viewteacher(request):
    std=teacher.objects.all()
    return render(request,'viewteacher.html',{'result':std})

def viewhod(request):
    std=hodtable.objects.all()
    return render(request,'viewhod.html',{'result':std})

def feedback(request):
    feedback_status = FeedbackStatus.objects.first()
    current_time = now()

    print("Current Time:", current_time)  # ✅ Print current server time
    print("Feedback Start Time:", feedback_status.start_time)
    print("Feedback End Time:", feedback_status.end_time)
    print("Is Active:", feedback_status.is_active)

    # Check if feedback is active and within the allowed time range
    if not feedback_status.is_active:
        return render(request, "feedback_closed.html")  # Redirect to feedback closed page

    sname = request.session.get('sname')  # Get student name from session
    given_feedback_teachers = Feedback.objects.filter(user_id=sname).values_list('teacher_id', flat=True)
    
    # Fetch only those teachers who haven't received feedback from this student
    teachers = teacher.objects.exclude(id__in=given_feedback_teachers)

    return render(request, 'feedback.html', {'teachers': teachers})
def addfeedback(request):
    if request.method == 'POST':
        sname = request.session.get('sname')  # Use .get() to prevent KeyError
        teacher_id = request.POST.get('teacher_id')
        feedback_text = request.POST.get('feedback')

        if sname and teacher_id and feedback_text:
            try:
                teacher_obj = teacher.objects.get(id=teacher_id)  # Ensure correct model name
                Feedback.objects.create(user_id=sname, feedback=feedback_text, teacher=teacher_obj)
            except teacher.DoesNotExist:
                return render(request, "feedback.html", {'error': 'Invalid teacher selected'})

        return redirect('feedback')  # Redirect to clear form and reload data

    teachers = teacher.objects.all()  # Fetch teachers again
    return render(request, "feedback.html", {'teachers': teachers})

def viewfeedback(request):
    feedback_status = FeedbackStatus.objects.first()
    feedbacks = Feedback.objects.all()
    return render(request, "viewfeedback.html", {"result": feedbacks, "feedback_status": feedback_status})



def generate_feedback_pdf():
    feedbacks = Feedback.objects.all()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 800, "Feedback Report")
    y = 780

    for feedback in feedbacks:
        pdf.drawString(100, y, f"Student: {feedback.user_id},Teacher: {feedback.teacher.name}, Feedback: {feedback.feedback}")
        y -= 20

    pdf.showPage()
    pdf.save()

    pdf_data = buffer.getvalue()
    buffer.close()

    filename = f"feedback_{now().strftime('%Y-%m-%d')}.pdf"
    feedback_status = FeedbackStatus.objects.first()
    
    if feedback_status:
        feedback_status.generated_pdf.save(filename, ContentFile(pdf_data))
        feedback_status.save()



def enable_feedback(request):
    if request.method == "POST":
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        if start_time and end_time:
            FeedbackStatus.objects.update_or_create(
                id=1,  # Ensure only one feedback session exists
                defaults={
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_active": True
                }
            )
            Feedback.objects.all().delete() 
            messages.success(request, "Feedback has been enabled successfully!")
        else:
            messages.error(request, "Invalid time range.")

    return redirect("view_feedback_page")

def disable_feedback(request):
    feedback_status = FeedbackStatus.objects.first()
    if feedback_status:
        feedback_status.is_active = False
        feedback_status.save()
        generate_feedback_pdf()
        messages.success(request, "Feedback has been disabled.")

    return redirect("view_feedback_page")

def feedback_page(request):
    feedback_status = FeedbackStatus.objects.first()
    current_time = now()

    if feedback_status and feedback_status.is_active and feedback_status.start_time <= current_time <= feedback_status.end_time:
        return render(request, "feedback.html")  # Feedback page is accessible
    else:
        return render(request, "feedback_closed.html")
    
# def viewstudent(request):
#     return render(request,'viewstudent.html')
def viewstudent(request):
    fdb=student_table.objects.all()
    return render(request,'viewstudent.html',{'result':fdb})  

def delete(request, id):
    # Try deleting from student_table
    student = student_table.objects.filter(id=id).first()
    if student:
        student.delete()
        return redirect(viewstudent)  # Ensure `viewstudent` is correctly defined
    
    # Try deleting from teacher
    teacher_obj = teacher.objects.filter(id=id).first()
    if teacher_obj:
        teacher_obj.delete()
        return redirect(viewteacher)
    
    
    hod_obj = hodtable.objects.filter(id=id).first()
    if hod_obj:
        hod_obj.delete()
        return redirect(viewhod)

    # If ID not found in either table, handle the case (optional)
    return redirect(viewstudent)  # Redirect even if no match is found 

def notes(request):
    return render(request,'notes.html')

def addnotes(request):
    myfiles=request.FILES['notes']
    fs=FileSystemStorage()
    filepath=fs.save(myfiles.name,myfiles)
    
def profile(request):
    user_type = None
    user_data = None

    if 'hid' in request.session:
        user_type = 'hod'
        user_data = get_object_or_404(hodtable, id=request.session['hid'])
    
    elif 'tid' in request.session:
        user_type = 'teacher'
        user_data = get_object_or_404(teacher, id=request.session['tid'])

    elif 'sid' in request.session:
        user_type = 'student'
        user_data = get_object_or_404(student_table, id=request.session['sid'])

    if not user_data:
        return redirect('login')

    return render(request, 'profile.html', {
        'user_data': user_data,
        'user_type': user_type,
    })

def progress_report(request):
    student_id = request.session.get("sid")

    if not student_id:
        return redirect('login')

    student = get_object_or_404(student_table, id=student_id)

    mcq_scores = StudentExamScore.objects.filter(student=student_id).values_list('tgpa_exam', flat=True)
    mcq_scores = [score for score in mcq_scores if score is not None]
    avg_tgpa_mcq = round(mean(mcq_scores), 2) if mcq_scores else 0

    subjective_scores = StudentResponse.objects.filter(student=student_id).values_list('tgpa', flat=True)
    subjective_scores = [score for score in subjective_scores if score is not None]
    avg_tgpa_subjective = round(mean(subjective_scores), 2) if subjective_scores else 0

    return render(request, 'progress_report.html', {
        'student_name': student.name,
        'avg_tgpa_mcq': avg_tgpa_mcq,
        'avg_tgpa_subjective': avg_tgpa_subjective
    })

def add_subject(request):
    if request.method == "POST":
        semester_id = request.POST.get('semester')
        subject_name = request.POST.get('name')
        course_code = request.POST.get('course_code')
        teacher_id = request.POST.get('teacher')

        if semester_id and subject_name:
            semester = Semester.objects.get(id=semester_id)
            assigned_teacher = get_object_or_404(teacher, id=teacher_id)
            Subject.objects.create(semester=semester, name=subject_name, course_code=course_code,teacher=assigned_teacher)
            messages.success(request, "Subject added successfully!")
        else:
            messages.error(request, "All fields are required!")

        return redirect('add_subject')

    semesters = Semester.objects.all()
    teachers = teacher.objects.all()
    return render(request, 'add_subject.html', {'semesters': semesters, 'teachers': teachers})

def semester_subjects(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id)
    subjects = semester.subjects.select_related('teacher').all()
    return render(request, 'subject.html', {'semester': semester, 'subjects': subjects})


def home(request):
    semesters = Semester.objects.all()
    return render(request, 'home.html', {'semesters': semesters})

def modules(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    modules = subject.module_set.all()

    # Retrieve logged-in teacher ID or HOD ID from session
    teacher_id = request.session.get('tid', None)
    hid = request.session.get('hid', None)  # HOD ID (for HOD access)
    is_assigned_teacher = False

    # Check if the logged-in teacher is the assigned teacher
    assigned_teacher = None
    if teacher_id:
        try:
            assigned_teacher = teacher.objects.get(id=teacher_id)
            is_assigned_teacher = (subject.teacher.id == assigned_teacher.id)
        except teacher.DoesNotExist:
            pass  # Keep is_assigned_teacher as False if teacher is not found

    # Allow file upload only for assigned teacher OR HOD
    if request.method == 'POST' and request.FILES.get('file'):
        if not is_assigned_teacher and not hid:  # Restrict access
            messages.error(request, "You are not authorized to upload notes for this subject.")
            return redirect('modules', subject_id=subject_id)

        module_id = request.POST.get('module_id')
        file = request.FILES['file']
        file_name = request.POST.get('file_name')
        module = get_object_or_404(Module, id=module_id)

        # Save uploaded file
        Note.objects.create(file=file, module=module, file_name=file_name)
        messages.success(request, "Note uploaded successfully!")

    return render(request, 'modules.html', {
        'subject': subject,
        'modules': modules,
        'is_assigned_teacher': is_assigned_teacher
    })

def note_list(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    notes = module.note_set.all() 
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        Note.objects.create(file=file, module=module)
    return render(request, 'note_list.html', {'module': module, 'notes': notes})

def progress_report(request):
    """Display overall progress report combining MCQ and Subjective TGPA."""
    student_id = request.session.get("sid")

    if not student_id:
        return redirect('login')

    student = get_object_or_404(student_table, id=student_id)

    # **Retrieve latest TGPA per MCQ test**
    mcq_tests = (
        StudentExamScore.objects.filter(student=student_id, question_type="MCQ")
        .values("test_title")
        .annotate(latest_tgpa=Max("tgpa_exam"))  
    )

    mcq_scores = [test["latest_tgpa"] for test in mcq_tests if test["latest_tgpa"] is not None]
    avg_tgpa_mcq = round(mean(mcq_scores), 2) if mcq_scores else 0

    # **Retrieve latest TGPA per Subjective test**
    subjective_tests = (
        StudentResponse.objects.filter(student=student_id)
        .values("exam_title")
        .annotate(latest_tgpa=Max("tgpa"))  
    )

    subjective_scores = [test["latest_tgpa"] for test in subjective_tests if test["latest_tgpa"] is not None]
    avg_tgpa_subjective = round(mean(subjective_scores), 2) if subjective_scores else 0

    # **Calculate Total TGPA**
    total_tgpa = round((avg_tgpa_mcq + avg_tgpa_subjective) / 2, 2)

    return render(request, 'progress_report.html', {
        'student_name': student.name,
        'avg_tgpa_mcq': avg_tgpa_mcq,
        'avg_tgpa_subjective': avg_tgpa_subjective,
        'total_tgpa': total_tgpa,  
        'mcq_tests': list(mcq_tests),  # ✅ Pass structured MCQ data
        'subjective_tests': list(subjective_tests)  # ✅ Pass structured Subjective data
    })