"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from mysite.views import (CourseView, TimetableView, AttendanceView, account,
                          attendance_summary, change_password, create_attendance_session,
                          close_attendance_session, join_course, mark_session_attendance,
                          regenerate_join_code, register, register_teacher, student_courses,
                          student_timetable, teacher_attendance_report, teacher_slot,
                          teacher_courses, verify_registration, health)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView)
router = DefaultRouter()
router.register(r'courses', CourseView,basename='course')
router.register(r'timetables', TimetableView,basename='timetable')
router.register(r'attendances', AttendanceView,basename='attendance')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/health/', health, name='health'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', register, name='register'),
    path('api/register/teacher/', register_teacher, name='register-teacher'),
    path('api/attendance-summary/', attendance_summary, name='attendance-summary'),
    path('api/register/verify/', verify_registration, name='verify-registration'),
    path('api/account/', account, name='account'),
    path('api/account/password/', change_password, name='change-password'),
    path('api/teacher/courses/', teacher_courses, name='teacher-courses'),
    path('api/teacher/courses/<int:course_id>/regenerate-code/', regenerate_join_code, name='regenerate-code'),
    path('api/teacher/courses/<int:course_id>/slots/', teacher_slot, name='teacher-slots'),
    path('api/teacher/courses/<int:course_id>/attendance/', teacher_attendance_report, name='teacher-report'),
    path('api/teacher/slots/<int:slot_id>/attendance-session/', create_attendance_session, name='create-attendance-session'),
    path('api/teacher/attendance-sessions/<int:session_id>/close/', close_attendance_session, name='close-attendance-session'),
    path('api/student/courses/', student_courses, name='student-courses'),
    path('api/student/courses/join/', join_course, name='join-course'),
    path('api/student/timetable/', student_timetable, name='student-timetable'),
    path('api/student/attendance/mark/', mark_session_attendance, name='mark-session-attendance'),
]
