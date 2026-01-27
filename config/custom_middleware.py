from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class AuctionAccessMiddleware(BaseMiddleware):
    """
    [확장성] 웹소켓 연결 시 보안 검사
    1. 로그인 여부 확인
    2. (선택) 특정 채팅방/경매장 접근 권한 확인
    """
    async def __call__(self, scope, receive, send):
        # 1. 로그인 여부 확인 (AuthMiddlewareStack이 먼저 처리했다고 가정하지만 한번 더 체크 가능)
        user = scope.get('user')
        
        if not user or user.is_anonymous:
            # (옵션) 쿼리 파라미터로 오는 토큰 처리 등 추가 가능
            pass
            
        # 2. 여기서 추가적인 권한 검사를 수행할 수 있음
        # 예: scope['url_route']['kwargs']['room_name'] 을 확인하여 
        # 해당 경매방이 존재하는지, 블랙리스트 유저는 아닌지 등.
        
        return await super().__call__(scope, receive, send)
