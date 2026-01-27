# auctions/models.py

from django.db import models
from django.conf import settings
from common.models import Region, Category
from django.core.validators import FileExtensionValidator

class Auction(models.Model):
    # 판매자 (User와 연결)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_auctions')
    
    # 상품 정보
    title = models.CharField(max_length=100) # 상품명
    description = models.TextField() # 상세 설명
    
    # [보안] 이미지 확장자 검증 추가
    image = models.ImageField(
        upload_to='auction_images/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    ) 
    
    # 가격 설정 (음수 방지를 위해 PositiveIntegerField 사용)
    start_price = models.PositiveIntegerField() # 시작가
    current_price = models.PositiveIntegerField(default=0) # 현재가 (입찰 들어오면 변함)
    instant_price = models.PositiveIntegerField(blank=True, null=True) # 즉시 구매가 (선택사항)
    bid_unit = models.PositiveIntegerField(default=1000) # 입찰 단위 (예: 1000원 단위로 입찰)
    # [추가] 이 상품을 찜한 사람들 (User와 N:M 관계)
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='watchlist', blank=True)
    # 시간 설정
    start_time = models.DateTimeField() # 경매 시작 시간
    end_time = models.DateTimeField() # 경매 종료 시간
    
    # 경매 상태 (진행중, 종료, 유찰 등)
    STATUS_CHOICES = (
        ('WAITING', '대기중'),
        ('ACTIVE', '진행중'),
        ('ENDED', '종료됨'),
        ('CANCELLED', '취소됨'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='WAITING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    # [추가] 판매 지역 (기본적으로 판매자의 지역을 따라감)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)

    # [추가] 전국 실시간 경매 여부
    # True: 웹소켓+Redis 사용 (전국 노출)
    # False: 일반 DB 트랜잭션 사용 (지역 한정)
    is_national = models.BooleanField(default=False, verbose_name="전국 실시간 경매")

    # [추가] 낙찰자 (경매 종료 시 확정)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='won_auctions',
        verbose_name="낙찰자"
    )
    
    # [추가] 카테고리
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    # [추가] 상품 상태 (새상품, 중고 등)
    CONDITION_CHOICES = [
        ('NEW', '새 상품'),
        ('USED_S', 'S급 (미사용)'),
        ('USED_A', 'A급 (사용감 적음)'),
        ('USED_B', 'B급 (보통)'),
        ('USED_C', 'C급 (하자 있음)'),
    ]
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='USED_A')

    # [추가] 배송비 부담
    SHIPPING_CHOICES = [
        ('SELLER', '판매자 부담 (무료배송)'),
        ('BUYER', '구매자 부담 (착불)'),
    ]
    shipping_payer = models.CharField(max_length=10, choices=SHIPPING_CHOICES, default='BUYER')

    def __str__(self):
        return f"[{self.status}] {self.title}"
    

# auctions/models.py (맨 아래에 추가)
class Bid(models.Model):
    # 어떤 경매에 대한 입찰인지
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    
    # 입찰자 (User)
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids')
    
    # 입찰 금액
    amount = models.PositiveIntegerField()
    
    # 입찰 시간
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} - {self.amount}원 입찰"
    
# auctions/models.py 맨 아래 추가

class Comment(models.Model):
    # 어떤 경매에 달린 댓글인지
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='comments')
    # 누가 썼는지
    writer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # 내용
    content = models.TextField()
    # 작성일
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.writer} - {self.content[:20]}"
