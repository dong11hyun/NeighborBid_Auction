# auctions/services.py (새로 만들기)

from django.db import transaction
from django.utils import timezone
from .models import Auction, Bid
from wallet.models import Wallet, Transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def place_bid(auction_id, user, amount):
    """
    입찰을 수행하는 핵심 함수 (트랜잭션 적용)
    """
    with transaction.atomic():
        # 1. 경매 정보를 가져오되, 동시성 문제를 막기 위해 'Lock'을 겁니다.
        # (누가 입찰하는 동안 다른 사람은 이 경매 정보를 수정 못하게 막음)
        auction = Auction.objects.select_for_update().get(id=auction_id)
        
        # 경매 상태 확인
        if auction.status != 'ACTIVE':
            raise ValueError("진행 중인 경매가 아닙니다.")
        
        if auction.end_time < timezone.now():
            raise ValueError("이미 종료된 경매입니다.")
            
        # 가격 검증 (현재가 + 입찰단위보다 높아야 함)
        min_bid_price = auction.current_price + auction.bid_unit
        # (첫 입찰인 경우 시작가보다 높아야 함)
        if auction.current_price == 0:
            min_bid_price = auction.start_price
            
        if amount < min_bid_price:
            raise ValueError(f"최소 {min_bid_price}원 이상 입찰해야 합니다.")

        # ============================================
        # 여기서부터 진짜 돈 처리 (가장 중요!)
        # ============================================

        # 2. 이전 최고 입찰자가 있다면 돈 돌려주기 (잠금 해제)
        # 현재가(current_price)가 0이 아니고, 입찰 기록이 있다면
        if auction.current_price > 0:
            last_bid = auction.bids.order_by('-amount').first()
            if last_bid:
                prev_bidder_wallet = Wallet.objects.select_for_update().get(user=last_bid.bidder)
                
                # 묶여있던 돈(locked)을 다시 잔액(balance)으로 이동
                prev_bidder_wallet.locked_balance -= last_bid.amount
                prev_bidder_wallet.balance += last_bid.amount
                prev_bidder_wallet.save()
                
                # 로그 남기기
                Transaction.objects.create(
                    wallet=prev_bidder_wallet,
                    amount=last_bid.amount,
                    transaction_type='BID_REFUND',
                    description=f"경매({auction.title}) 상위 입찰 발생으로 환불"
                )    

        # 입찰자의 지갑 확인
        wallet = Wallet.objects.select_for_update().get(user=user)
        if wallet.balance < amount:
            raise ValueError("잔액이 부족합니다.")
        
        # 3. 내 돈 잠그기 (지갑에서 차감 -> 잠금으로 이동)
        wallet.balance -= amount
        wallet.locked_balance += amount
        wallet.save()
        
        Transaction.objects.create(
            wallet=wallet,
            amount=-amount, # 내역에는 음수로 표시하거나 0으로 표시 (잠금이니까)
            transaction_type='BID_LOCK',
            description=f"경매({auction.title}) 입찰 예약금"
        )

        # 4. 입찰 기록 생성
        Bid.objects.create(
            auction=auction,
            bidder=user,
            amount=amount
        )

        # 5. 경매 현재가 업데이트
        auction.current_price = amount
        auction.save()

        return f"성공! {amount}원에 입찰했습니다."
    
# auctions/services.py (맨 아래에 추가)

def determine_winner(auction_id):
    """
    경매 종료 시 낙찰자를 확정하고 돈을 이동시키는 함수
    """
    with transaction.atomic():
        auction = Auction.objects.select_for_update().get(id=auction_id)
        
        # 이미 종료된 거면 패스
        if auction.status != 'ACTIVE':
            return "이미 종료된 경매입니다."
            
        # 낙찰자 결정
        winning_bid = auction.bids.order_by('-amount').first()
        
        if winning_bid:
            # 1. 낙찰자 지갑 가져오기
            winner_wallet = Wallet.objects.select_for_update().get(user=winning_bid.bidder)
            
            # 2. 판매자 지갑 가져오기
            seller_wallet = Wallet.objects.select_for_update().get(user=auction.seller)
            
            # 3. 돈 이동 (낙찰자 잠금해제 -> 차감 -> 판매자에게 입금)
            # 낙찰자는 이미 입찰할 때 돈이 locked_balance에 묶여있음
            winner_wallet.locked_balance -= winning_bid.amount
            winner_wallet.save()
            
            seller_wallet.balance += winning_bid.amount
            seller_wallet.save()
            
            # 4. 거래 기록 남기기
            # 낙찰자 출금 기록
            Transaction.objects.create(
                wallet=winner_wallet,
                amount=-winning_bid.amount,
                transaction_type='PAYMENT',
                description=f"경매 낙찰 결제 ({auction.title})"
            )
            # 판매자 입금 기록
            Transaction.objects.create(
                wallet=seller_wallet,
                amount=winning_bid.amount,
                transaction_type='EARNING',
                description=f"경매 판매 수익 ({auction.title})"
            )
            
            auction.status = 'ENDED'
            auction.save()
            return f"낙찰 확정! {winning_bid.bidder.username}님이 {winning_bid.amount}원에 낙찰받았습니다."
            
        else:
            # 입찰자가 아무도 없으면 '유찰' 처리
            auction.status = 'ENDED' # 혹은 CANCELLED
            auction.save()
            return "입찰자가 없어 유찰되었습니다."


# auctions/services.py (맨 아래에 추가)

def buy_now(auction_id, buyer):
    """
    즉시 구매 함수 (수정됨: transaction.on_commit 적용 + 디버깅 로그)
    """
    # 1. 먼저 채널 레이어 함수 정의 (트랜잭션 바깥에서 실행될 함수)
    def send_sold_out_notification():
        print(f"📡 [Debug] 즉시 구매 알림 전송 시작: Auction ID {auction_id}")
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'auction_{auction_id}',
                {
                    'type': 'auction_end_notification',
                    'bidder': buyer.username,
                    'amount': instant_price_val, # 아래에서 캡처한 변수 사용
                    'msg': f"📢 {buyer.username}님이 {instant_price_val}원에 즉시 구매하셨습니다! (경매 종료)"
                }
            )
            print("✅ [Debug] 알림 전송 완료")
        except Exception as e:
            print(f"❌ [Debug] 알림 전송 실패: {e}")

    with transaction.atomic():
        # 1. 경매 정보 가져오기 (Lock)
        auction = Auction.objects.select_for_update().get(id=auction_id)
        
        # 값을 미리 변수에 저장 (on_commit에서 쓰기 위함)
        instant_price_val = auction.instant_price

        if auction.status != 'ACTIVE':
            raise ValueError("진행 중인 경매가 아닙니다.")
        if not auction.instant_price:
            raise ValueError("즉시 구매가 불가능한 상품입니다.")
        if buyer == auction.seller:
            raise ValueError("판매자는 자신의 물건을 구매할 수 없습니다.")
        
        # 2. 구매자 지갑 가져오기
        buyer_wallet = Wallet.objects.select_for_update().get(user=buyer)
        
        # 3. 현재 1등 입찰자 확인
        current_highest_bid = auction.bids.order_by('-amount').first()
        
        # 자금력 검증
        available_funds = buyer_wallet.balance
        if current_highest_bid and current_highest_bid.bidder == buyer:
            available_funds += current_highest_bid.amount

        if available_funds < auction.instant_price:
            raise ValueError(f"잔액이 부족합니다. (필요: {auction.instant_price}원)")

        # 4. 기존 입찰자 환불
        if current_highest_bid:
            prev_wallet = Wallet.objects.select_for_update().get(user=current_highest_bid.bidder)
            prev_wallet.locked_balance -= current_highest_bid.amount
            prev_wallet.balance += current_highest_bid.amount
            prev_wallet.save()
            
            Transaction.objects.create(
                wallet=prev_wallet,
                amount=current_highest_bid.amount,
                transaction_type='BID_REFUND',
                description=f"경매({auction.title}) 즉시 구매로 인한 입찰금 반환"
            )

        # 5. 구매자 결제
        buyer_wallet.refresh_from_db() 
        buyer_wallet.balance -= auction.instant_price
        buyer_wallet.save()

        seller_wallet = Wallet.objects.select_for_update().get(user=auction.seller)
        seller_wallet.balance += auction.instant_price
        seller_wallet.save()

        # 6. 거래 기록 및 종료 처리
        Transaction.objects.create(wallet=buyer_wallet, amount=-auction.instant_price, transaction_type='PAYMENT', description=f"즉시 구매 결제 ({auction.title})")
        Transaction.objects.create(wallet=seller_wallet, amount=auction.instant_price, transaction_type='EARNING', description=f"즉시 구매 판매 수익 ({auction.title})")

        auction.current_price = auction.instant_price
        auction.winner = buyer
        auction.status = 'ENDED'
        auction.save()

        # ==========================================================
        # [핵심 수정] 트랜잭션이 '성공적으로 커밋된 후'에 메시지를 보냅니다.
        # 이렇게 해야 DB 충돌을 방지하고, 확실하게 처리된 후에만 알림이 갑니다.
        # ==========================================================
        transaction.on_commit(send_sold_out_notification)
    return f"축하합니다! {auction.title} 상품을 즉시 구매했습니다."