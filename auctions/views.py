# auctions/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Auction
from .services import place_bid # 아까 만든 입찰 로직 가져오기
from wallet.models import Wallet, Transaction 
from .models import Bid
from .forms import AuctionForm # 파일 맨 위에 이거 꼭 추가하세요!

# 경매 목록 조회
def auction_list(request):
    # 1. 기본적으로 진행중/대기중인 경매만 가져옴
    auctions = Auction.objects.filter(status__in=['ACTIVE', 'WAITING'])
    
    # 2. 검색어('q')가 있으면 필터링
    query = request.GET.get('q')
    if query:
        # 제목(title)에 검색어가 포함되어 있으면 가져옴 (icontains는 대소문자 무시)
        auctions = auctions.filter(title__icontains=query)

    # 3. 정렬 순서('sort') 처리
    sort = request.GET.get('sort', 'recent') # 기본값은 최신순
    
    if sort == 'price_asc': # 가격 낮은순
        auctions = auctions.order_by('current_price')
    elif sort == 'price_desc': # 가격 높은순
        auctions = auctions.order_by('-current_price')
    elif sort == 'end_soon': # 마감 임박순
        auctions = auctions.order_by('end_time')
    else: # recent (최신순)
        auctions = auctions.order_by('-created_at')

    return render(request, 'auctions/auction_list.html', {
        'auctions': auctions,
        'sort': sort # 현재 어떤 정렬인지 템플릿에 알려줌
    })

# 상세 조회 및 입찰하기
@login_required # 로그인한 사람만 볼 수 있음
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # 입찰 버튼을 눌렀을 때 (POST 요청)
    if request.method == 'POST':
        amount = int(request.POST.get('amount'))
        try:
            # 우리가 만든 핵심 로직 호출!
            msg = place_bid(auction.id, request.user, amount)
            messages.success(request, msg) # 성공 메시지
        except ValueError as e:
            messages.error(request, str(e)) # 실패 메시지 (돈 부족 등)
            
        return redirect('auction_detail', auction_id=auction.id)

    return render(request, 'auctions/auction_detail.html', {'auction': auction})

# 내 경매 관리 및 참여 경매 관리
@login_required
def mypage(request):
    # 1. 내가 입찰한 경매들 (최신순)
    my_bids = Bid.objects.filter(bidder=request.user).select_related('auction').order_by('-created_at')
    
    # 2. 내가 올린 경매들
    my_auctions = Auction.objects.filter(seller=request.user).order_by('-created_at')
    
    # 3. 내 지갑 정보 가져오기 (없으면 생성)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    return render(request, 'auctions/mypage.html', {
        'my_bids': my_bids,
        'my_auctions': my_auctions,
        'wallet': wallet
    })

# 재화 충전 (간이 버전)
@login_required
def charge_wallet(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount', 0))
        if amount > 0:
            wallet = Wallet.objects.get(user=request.user)
            wallet.balance += amount
            wallet.save()
            
            # 충전 기록 남기기
            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='DEPOSIT',
                description='마이페이지에서 충전'
            )
            messages.success(request, f"{amount}원이 충전되었습니다! 💵")
    return redirect('mypage')


# 경매 개설
@login_required
def auction_create(request):
    if request.method == 'POST':
        # 사용자가 입력한 데이터(POST)와 파일(FILES)을 폼에 채워넣음
        form = AuctionForm(request.POST, request.FILES)
        
        if form.is_valid():
            auction = form.save(commit=False) # 잠시 저장을 미룸 (추가 정보 입력을 위해)
            auction.seller = request.user     # 판매자는 '현재 로그인한 사람'
            auction.current_price = 0         # 현재가는 0원부터
            auction.status = 'ACTIVE'         # 바로 '진행중' 상태로 시작 (테스트용)
            
            # 조건 검증 (예: 시작 시간 < 종료 시간)
            if auction.start_time >= auction.end_time:
                messages.error(request, "종료 시간은 시작 시간보다 뒤여야 합니다.")
                return render(request, 'auctions/auction_form.html', {'form': form})
                
            auction.save() # 진짜 저장
            messages.success(request, "경매가 성공적으로 등록되었습니다! 🎉")
            return redirect('auction_list')
    else:
        # 처음 들어왔을 때는 빈 폼을 보여줌
        form = AuctionForm()
        
    return render(request, 'auctions/auction_form.html', {'form': form})