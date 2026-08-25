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
                          attendance_summary, change_password, register,
                          verify_registration)
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
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', register, name='register'),
    path('api/attendance-summary/', attendance_summary, name='attendance-summary'),
    path('api/register/verify/', verify_registration, name='verify-registration'),
    path('api/account/', account, name='account'),
    path('api/account/password/', change_password, name='change-password'),
]
