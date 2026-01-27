from celery import shared_task
from django.utils import timezone
from .models import Auction
from .services import determine_winner

@shared_task
def check_expired_auctions():
    """
    1분마다 실행되며, 종료 시간이 지났는데 아직 status가 ACTIVE인 경매를 종료 처리함
    """
    now = timezone.now()
    
    # 종료 시간이 지났고 + 상태가 아직 ACTIVE인 경매들
    expired_auctions = Auction.objects.filter(
        end_time__lte=now,
        status='ACTIVE'
    )
    
    results = []
    for auction in expired_auctions:
        # 서비스 로직을 재사용하여 낙찰 처리
        msg = determine_winner(auction.id)
        results.append(f"Auction {auction.id}: {msg}")
        
    return results
