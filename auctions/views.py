# auctions/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Auction
from .services import place_bid 
from wallet.models import Wallet, Transaction 
from .models import Bid
from .forms import AuctionForm, CommentForm 
from django.db.models import Q 
from common.models import Region, Category 

# 특정 지역의 하위 지역(자식, 손자 등) ID를 재귀적으로 찾는 함수.
def get_all_descendants(region):
    descendants = []
    children = region.sub_regions.all()
    for child in children:
        descendants.append(child)
        # 재귀 호출: 자식의 자식들을 계속 찾아옴
        descendants.extend(get_all_descendants(child))
    return descendants

# 경매 목록 조회 + 필터링(지역/카테고리/가격)
def auction_list(request):
    # 1. 기본: '진행중'이거나 '대기중'인 경매만 가져옴
    auctions = Auction.objects.filter(status__in=['ACTIVE', 'WAITING'])
    
    # === [필터 1] 지역 (Region) ===
    region_id = request.GET.get('region') #안전하게 꺼내기 .get()
    selected_region = None
    
    if region_id:
        try:
            selected_region = Region.objects.get(id=region_id)
            
            # [수정됨] 직계 자식뿐만 아니라 '모든 하위 지역(손자 포함)'을 가져오도록 변경
            # 예: '서울' 선택 -> '서울' + '영등포구' + '신길동' + '대림동' ... 모두 포함
            regions_to_check = [selected_region] + get_all_descendants(selected_region)
            
            auctions = auctions.filter(
                Q(region__in=regions_to_check) | Q(is_national=True)
            )
        except Region.DoesNotExist:
            pass

    # === [필터 2] 카테고리 (Category) ===
    category_slug = request.GET.get('category')
    if category_slug:
        auctions = auctions.filter(category__slug=category_slug)

    # === [필터 3] 가격 범위 (Price) ===
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        auctions = auctions.filter(current_price__gte=min_price)
    if max_price:
        auctions = auctions.filter(current_price__lte=max_price)

    # === [검색 및 정렬] ===
    query = request.GET.get('q')
    if query:
        auctions = auctions.filter(title__icontains=query)

    sort = request.GET.get('sort', 'recent')
    if sort == 'price_asc':
        auctions = auctions.order_by('current_price')
    elif sort == 'price_desc':
        auctions = auctions.order_by('-current_price')
    elif sort == 'end_soon':
        auctions = auctions.order_by('end_time')
    else:
        auctions = auctions.order_by('-created_at')

    # [수정됨] 사이드바 데이터 준비
    # 기존: depth__lte=2 (구 까지만 보여줌) -> 문제: 동이 안 보임
    # 변경: 모든 지역을 다 보여주거나, 로직을 개선
    # 지금은 MVP 단계이므로 '전체 지역'을 가져오되, 보기 좋게 정렬합니다.
    # (나중에 데이터가 많아지면 Ajax로 펼치기 기능을 구현해야 합니다)
    all_regions = Region.objects.all().order_by('depth', 'parent__id', 'name')
    
    all_categories = Category.objects.all()

    context = {
        'auctions': auctions,
        'all_regions': all_regions,
        'all_categories': all_categories,
        'selected_region': selected_region,
        'sort': sort,
    }
    return render(request, 'auctions/auction_list.html', context)

# 상세 조회 및 입찰하기
@login_required # 로그인한 사람만 볼 수 있음
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # [추가] 이 판매자가 올린 '다른' 경매 물품들 (최신순 4개)
    other_items = Auction.objects.filter(seller=auction.seller, status='ACTIVE').exclude(id=auction_id).order_by('-created_at')[:4]

    context = {
        'auction': auction,
        'other_items': other_items, # 템플릿으로 전달
    }
    
    # 입찰 버튼을 눌렀을 때 (POST 요청)
    if request.method == 'POST':
        # 수정 3 판매자가 입찰 시 본인 물건 낙찰 방지 -> 판매자 입찰 불가능하게 막음
        if request.user == auction.seller:
            messages.error(request, "판매자는 본인의 경매에 입찰할 수 없습니다.")
            return redirect('auction_detail', auction_id=auction.id)
        
        amount = int(request.POST.get('amount'))
        try:
            # 우리가 만든 핵심 로직 호출!
            msg = place_bid(auction.id, request.user, amount)
            messages.success(request, msg) # 성공 메시지
        except ValueError as e:
            messages.error(request, str(e)) # 실패 메시지 (돈 부족 등)
            
        return redirect('auction_detail', auction_id=auction.id)
##### 버그 발견.?
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
            
            # 판매자의 지역 정보를 경매 상품에 자동 입력
            if request.user.region:
                auction.region = request.user.region

            auction.save() # 진짜 저장
            messages.success(request, "경매가 성공적으로 등록되었습니다! 🎉")
            return redirect('auction_list')
    else:
        # 처음 들어왔을 때는 빈 폼을 보여줌
        form = AuctionForm()
        
    return render(request, 'auctions/auction_form.html', {'form': form})


# auctions/views.py (맨 아래에 추가)
from .services import determine_winner

@login_required
def close_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # 판매자 본인만 종료 버튼을 누를 수 있게 함
    if request.user != auction.seller:
        messages.error(request, "판매자만 종료할 수 있습니다.")
        return redirect('auction_detail', auction_id=auction.id)
    
    # 로직 실행
    msg = determine_winner(auction.id)
    messages.info(request, msg)
    
    return redirect('auction_detail', auction_id=auction.id)

# auctions/views.py
from .services import determine_winner, buy_now  # buy_now 추가 import 확인!

# 즉시 구매 버튼 처리
@login_required
def auction_buy_now(request, auction_id):
    if request.method == 'POST':
        try:
            msg = buy_now(auction_id, request.user)
            messages.success(request, msg)
        except ValueError as e:
            messages.error(request, str(e))
    
    return redirect('auction_detail', auction_id=auction_id)

# auctions/views.py 맨 위에 from .forms import AuctionForm, CommentForm <- 추가!

# 맨 아래에 함수 추가
@login_required
def auction_comment(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.auction = auction
            comment.writer = request.user
            comment.save()
            messages.success(request, "문의가 등록되었습니다.")
            
    return redirect('auction_detail', auction_id=auction_id)


# auctions/views.py 맨 아래 추가

@login_required
def toggle_watchlist(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # 이미 찜한 상태면 -> 취소
    if auction.watchers.filter(id=request.user.id).exists():
        auction.watchers.remove(request.user)
        messages.info(request, "찜 목록에서 삭제했습니다.")
    # 찜 안 한 상태면 -> 추가
    else:
        auction.watchers.add(request.user)
        messages.success(request, "찜 목록에 추가했습니다! ❤️")
        
    return redirect('auction_detail', auction_id=auction_id)