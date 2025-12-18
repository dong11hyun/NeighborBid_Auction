# config/asgi.py

import os
import django

# [중요] 장고 설정 먼저 로드해야 models 접근 가능
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import auctions.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # websocket 요청은 -> 로그인 검사(Auth) -> 라우팅(URLRouter) -> 컨슈머로 전달
    "websocket": AuthMiddlewareStack(
        URLRouter(
            auctions.routing.websocket_urlpatterns
        )
    ),
})