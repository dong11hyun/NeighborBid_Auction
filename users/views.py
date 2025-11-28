# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from wallet.models import Wallet # 가입하면 지갑도 바로 만들어주기 위해

# 회원가입
def signup(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # [중요] 가입과 동시에 지갑 생성 (잔액 0원)
            Wallet.objects.create(user=user, balance=0)
            
            # 가입 후 바로 로그인 시켜주기
            login(request, user)
            return redirect('auction_list') # 메인 페이지로 이동
    else:
        form = RegisterForm()
        
    return render(request, 'users/signup.html', {'form': form})