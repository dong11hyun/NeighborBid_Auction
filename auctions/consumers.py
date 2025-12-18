# auctions/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Auction, Bid
from .services import place_bid # 기존 로직 재사용
from channels.db import database_sync_to_async

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # URL에서 auction_id 파싱 (ws://.../auction/1/)
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.room_group_name = f'auction_{self.auction_id}'

        # 1. 그룹(채팅방) 참여
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 연결 승인
        await self.accept()

    async def disconnect(self, close_code):
        # 그룹 탈퇴
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 2. 브라우저에서 입찰 요청을 보냈을 때 (Receive)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action') # 'bid' 같은 동작 구분

        if action == 'bid':
            amount = int(text_data_json['amount'])
            user = self.scope['user']

            # 로그인 안 한 유저 컷
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({'error': '로그인이 필요합니다.'}))
                return

            # [핵심] 입찰 처리 (DB 저장은 동기함수라 변환 필요)
            result_msg = await self.save_bid(self.auction_id, user, amount)
            
            if "성공" in result_msg:
                # 3. 성공 시 그룹 내 모든 사람에게 방송 (Broadcast)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'auction_update', # 아래 함수 실행
                        'amount': amount,
                        'bidder': user.username,
                        'msg': result_msg
                    }
                )
            else:
                # 실패 시 나한테만 에러 전송
                await self.send(text_data=json.dumps({'error': result_msg}))

    # 4. 그룹에서 메시지를 받았을 때 실제 전송 (Handler)
    async def auction_update(self, event):
        # 브라우저(JS)에게 최종 JSON 전송
        await self.send(text_data=json.dumps({
            'type': 'update',
            'amount': event['amount'],
            'bidder': event['bidder'],
            'msg': event['msg']
        }))

    # (비동기 래퍼) DB에 입찰 저장하는 함수 호출
    @database_sync_to_async
    def save_bid(self, auction_id, user, amount):
        try:
            # 기존 services.py의 place_bid 재활용 (강력 추천!)
            return place_bid(auction_id, user, amount)
        except ValueError as e:
            return str(e)