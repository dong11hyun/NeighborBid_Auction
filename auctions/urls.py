from django.urls import path
from . import views

urlpatterns = [
    path('', views.auction_list, name='auction_list'), # 메인 페이지
    path('auction/<int:auction_id>/', views.auction_detail, name='auction_detail'), # 상세 페이지
    # 새로 추가된 부분!
    path('mypage/', views.mypage, name='mypage'),
    path('wallet/charge/', views.charge_wallet, name='charge_wallet'),
    # 새로 추가!
    path('create/', views.auction_create, name='auction_create'),
]