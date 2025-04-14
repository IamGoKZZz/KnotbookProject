from django.db import models # type: ignore

class teacher(models.Model):
    email = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=150)
    experience = models.CharField(max_length=150)
    qualification = models.CharField(max_length=150)
    department = models.CharField(max_length=150)
    dob= models.CharField(max_length=150)
    idproof= models.FileField(max_length=255)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    
class hodtable(models.Model):
    email = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=150)
    experience = models.CharField(max_length=150)
    qualification = models.CharField(max_length=150)
    department = models.CharField(max_length=150)    
    idproof= models.FileField(max_length=255)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
class student_table(models.Model):
    email = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=150)
    dob = models.CharField(max_length=150)
    department = models.CharField(max_length=150)    
    idproof= models.FileField(max_length=255)
    age=models.CharField(max_length=5)
    status=models.CharField(max_length=150)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
   
    
class Department(models.Model):
    CSE = models.CharField(max_length=150)
    IT = models.CharField(max_length=150)
    EEE = models.CharField(max_length=150)
    MECH = models.CharField(max_length=150)
    ECE = models.CharField(max_length=150)
    
class Feedback(models.Model):
    user_id = models.CharField(max_length=150)
    teacher = models.ForeignKey("Teacher", on_delete=models.CASCADE)
    feedback = models.TextField()
    
class FeedbackStatus(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    generated_pdf = models.FileField(upload_to='feedback_pdfs/', null=True, blank=True)     


# class uploadnotes(models.Model):
#     image=models.FileField(max_length=250)
#     Subject_name=models.CharField(max_length=150)
    
class Semester(models.Model):
    name = models.CharField(max_length=100)  # e.g., S1 & S2
    description = models.TextField(blank=True, null=True) 
    
class Subject(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=20, blank=True, null=True)
    teacher=models.ForeignKey(teacher, on_delete=models.CASCADE, related_name='subjects')

class Module(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

class Note(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='notes/')
    #uploaded_by = models.CharField(max_length=100)  # Teacher name or ID
    uploaded_at = models.DateTimeField(auto_now_add=True)

  

# class assign_table(models.Model):
#     hod=models.CharField(max_length=150)
#     teacher=models.ForeignKey(teacher, on_delete=models.CASCADE)
#     subject=models.ForeignKey(Subject, on_delete=models.CASCADE)