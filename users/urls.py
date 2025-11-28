# users/urls.py (새로 만들기)

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 우리가 만든 회원가입
    path('signup/', views.signup, name='signup'),
    
    # 장고가 제공하는 로그인/로그아웃 (템플릿 위치만 알려주면 됨)
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]