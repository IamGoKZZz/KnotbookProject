
from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', views.first,name='first'),
    path('login/', views.login),
    path('login/addlogin', views.addlogin),
    path('login/logout',views.logout),
    path('logout',views.logout),
    path('home',views.home),
    path('tech',views.tech),
    path('addteacher',views.addteacher),
    path('addhod',views.addhod),
    path('hod',views.hod),
    path('student',views.student),
    path('addstudent',views.addstudent),
    path('viewstd',views.viewstd),
    path('viewteacher',views.viewteacher),
    path('viewhod',views.viewhod),
    path('feedback',views.feedback,name ='feedback'),
    path('enable_feedback/', views.enable_feedback, name='enable_feedback'),
    path('disable_feedback/', views.disable_feedback, name='disable_feedback'),
    path('addfeedback',views.addfeedback),
    path('viewfeedback',views.viewfeedback,name='view_feedback_page'),
    path('viewstudent',views.viewstudent),
    path('delete/<int:id>/',views.delete),
    path('notes',views.notes),
    path('addnotes',views.addnotes),
    path('add_subject/', views.add_subject, name='add_subject'),
    path('semesters/<int:semester_id>/', views.semester_subjects, name='semester_subjects'),
    path('home',views.home,name='home'),
    path('subjects/<int:subject_id>/', views.modules, name='modules'),
    path('modules/<int:module_id>/', views.note_list, name='note_list'),
    path('profile',views.profile),
    # path('assign',views.assign),
    path('test/',include('exam.urls')),
    path('progress-report/',views.progress_report, name='progress_report'),

    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


