# users/forms.py (새로 만들기)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        # 아이디, 이메일, 닉네임만 입력받음 (비밀번호는 UserCreationForm이 알아서 처리)
        fields = ['username', 'email', 'nickname']
        
        # 닉네임 입력칸 디자인
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '닉네임'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '아이디'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '이메일(선택)'}),
        }
        labels = {
            'username': '아이디',
            'email': '이메일',
            'nickname': '닉네임',
        }