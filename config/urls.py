# config/urls.py
from django.contrib import admin
from django.urls import path, include # include 추가!
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auctions.urls')), # 빈 주소('')로 접속하면 auctions 앱으로 보냄
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)