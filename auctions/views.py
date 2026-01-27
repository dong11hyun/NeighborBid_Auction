# auctions/views.py
from django.db import transaction # 트랜잭션 추가
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
        descendants.extend(get_all_descendants(child))
    return descendants


# 경매 목록 조회 + 필터링(지역/카테고리/가격)
def auction_list(request):
    # 1. 기본: '진행중'이거나 '대기중'인 경매만 가져옴
    # [최적화] select_related와 prefetch_related로 N+1 문제 해결
    auctions = Auction.objects.filter(
        status__in=['ACTIVE', 'WAITING']
    ).select_related(
        'seller', 'category', 'region'
    ).prefetch_related(
        'bids' # watchers는 당장 리스트에 안 쓰면 뺌
    ).order_by('-created_at')
    
    # === [필터 1] 지역 (Region) ===
    region_id = request.GET.get('region')
    selected_region = None
    
    if region_id:
        try:
            selected_region = Region.objects.get(id=region_id)
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

    # 사이드바 데이터 준비
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
@login_required 
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    other_items = Auction.objects.filter(seller=auction.seller, status='ACTIVE').exclude(id=auction_id).order_by('-created_at')[:4]

    context = {
        'auction': auction,
        'other_items': other_items,
    }
    
    # 입찰 버튼을 눌렀을 때 (POST 요청)
    if request.method == 'POST':
        if request.user == auction.seller:
            messages.error(request, "판매자는 본인의 경매에 입찰할 수 없습니다.")
            return redirect('auction_detail', auction_id=auction.id)
        
        # [검증 강화] 입력값 유효성 검사
        try:
            amount = int(request.POST.get('amount', 0))
            if amount <= 0:
                raise ValueError("입찰 금액은 0보다 커야 합니다.")
        except (ValueError, TypeError):
             messages.error(request, "유효하지 않은 입찰 금액입니다.")
             return redirect('auction_detail', auction_id=auction.id)

        try:
            msg = place_bid(auction.id, request.user, amount)
            messages.success(request, msg)
        except ValueError as e:
            messages.error(request, str(e))
            
        return redirect('auction_detail', auction_id=auction.id)

    return render(request, 'auctions/auction_detail.html',context)


# 내 경매 관리 및 참여 경매 관리
@login_required
def mypage(request):
    my_bids = Bid.objects.filter(bidder=request.user).select_related('auction').order_by('-created_at')
    my_auctions = Auction.objects.filter(seller=request.user).order_by('-created_at')
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
        
        # 금액 검증
        if amount <= 0 or amount > 10_000_000:
            messages.error(request, "유효하지 않은 충전 금액입니다.")
            return redirect('mypage')

        try:
            # [트랜잭션 추가]
            with transaction.atomic():
                # select_for_update로 동시성 제어
                wallet = Wallet.objects.select_for_update().get(user=request.user)
                wallet.balance += amount
                wallet.save()
                
                Transaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='DEPOSIT',
                    description='마이페이지에서 충전'
                )
            messages.success(request, f"{amount:,}원이 충전되었습니다! 💵")
        except Exception:
            messages.error(request, "충전 처리 중 오류가 발생했습니다.")
            
    return redirect('mypage')


# 경매 개설
@login_required
def auction_create(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST, request.FILES)
        
        if form.is_valid():
            auction = form.save(commit=False)
            auction.seller = request.user
            auction.current_price = 0
            auction.status = 'ACTIVE'
            
            if auction.start_time >= auction.end_time:
                messages.error(request, "종료 시간은 시작 시간보다 뒤여야 합니다.")
                return render(request, 'auctions/auction_form.html', {'form': form})
            
            if request.user.region:
                auction.region = request.user.region

            auction.save()
            messages.success(request, "경매가 성공적으로 등록되었습니다! 🎉")
            return redirect('auction_list')
    else:
        form = AuctionForm()
        
    return render(request, 'auctions/auction_form.html', {'form': form})


from .services import determine_winner, buy_now

@login_required
def close_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.user != auction.seller:
        messages.error(request, "판매자만 종료할 수 있습니다.")
        return redirect('auction_detail', auction_id=auction.id)
    
    msg = determine_winner(auction.id)
    messages.info(request, msg)
    
    return redirect('auction_detail', auction_id=auction.id)


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


@login_required
def toggle_watchlist(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    if auction.watchers.filter(id=request.user.id).exists():
        auction.watchers.remove(request.user)
        messages.info(request, "찜 목록에서 삭제했습니다.")
    else:
        auction.watchers.add(request.user)
        messages.success(request, "찜 목록에 추가했습니다! ❤️")
        
    return redirect('auction_detail', auction_id=auction_id)