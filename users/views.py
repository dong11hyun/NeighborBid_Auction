# users/views.py

from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from .forms import RegisterForm
from wallet.models import Wallet # 가입하면 지갑도 바로 만들어주기 위해
from auctions.models import Auction # Auction 모델 가져오기
from django.db.models import Avg
from django.contrib import messages
from .forms import ReviewForm
from .models import Review
from django.contrib.auth.decorators import login_required

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

@login_required
def create_review(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # [보안 검사]
    # 1. 낙찰자만 리뷰를 쓸 수 있음
    # winner 필드가 있으면 그것을 우선 사용
    is_winner = False
    if hasattr(auction, 'winner') and auction.winner:
        is_winner = (auction.winner == request.user)
    else:
        # winner 필드가 없는 경우(혹은 구버전 데이터) 입찰 기록으로 폴백
        last_bid = auction.bids.order_by('-amount').first()
        is_winner = (last_bid and last_bid.bidder == request.user)
    
    if not is_winner:
        messages.error(request, "낙찰자만 후기를 남길 수 있습니다.")
        return redirect('auction_detail', auction_id=auction.id)
    
    # 2. 이미 후기를 썼는지 확인
    if hasattr(auction, 'review'):
        messages.error(request, "이미 후기를 작성했습니다.")
        return redirect('auction_detail', auction_id=auction.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.seller = auction.seller
            review.auction = auction
            review.save()
            
            # [중요] 판매자 신용도 업데이트 로직
            # 판매자가 받은 모든 리뷰의 평점을 계산해서 업데이트
            avg_rating = Review.objects.filter(seller=auction.seller).aggregate(Avg('rating'))['rating__avg']
            
            # 100점 만점 환산 (5점 만점 * 20) or 그냥 5점 만점으로 저장
            # 여기서는 100점 만점 기준으로 환산해서 저장해봅시다.
            if avg_rating:
                new_score = int(avg_rating * 20) 
                auction.seller.reputation_score = new_score
                auction.seller.save()
            
            messages.success(request, "소중한 후기가 등록되었습니다! 판매자 신용도가 업데이트되었습니다.")
            return redirect('seller_profile', seller_id=auction.seller.id)
    else:
        form = ReviewForm()
        
    return render(request, 'users/create_review.html', {'form': form, 'auction': auction})