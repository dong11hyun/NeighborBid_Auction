# users/views.py

from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from .forms import RegisterForm
from wallet.models import Wallet # 가입하면 지갑도 바로 만들어주기 위해
from auctions.models import Auction # Auction 모델 가져오기

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

User = get_user_model()

def seller_profile(request, seller_id):
    seller = get_object_or_404(User, id=seller_id)
    
    # 이 판매자가 올린 물건들 (최신순)
    selling_auctions = Auction.objects.filter(seller=seller).order_by('-created_at')
    
    # 진행 중인 것과 종료된 것 분리 (선택사항)
    active_auctions = selling_auctions.filter(status='ACTIVE')
    closed_auctions = selling_auctions.exclude(status='ACTIVE')
    
    context = {
        'seller': seller,
        'active_auctions': active_auctions,
        'closed_auctions': closed_auctions,
    }
    return render(request, 'users/seller_profile.html', context)