# auctions/forms.py (새로 만들기)

from django import forms
from .models import Auction

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        # 사용자가 직접 입력해야 하는 필드만 골라줍니다.
        # (판매자, 현재가, 상태 등은 시스템이 알아서 채웁니다)
        fields = ['title', 'description', 'image', 'start_price', 'start_time', 'end_time']
        
        # 디자인(Bootstrap)을 입히기 위한 설정
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_price': forms.NumberInput(attrs={'class': 'form-control'}),
            # 날짜/시간 입력창을 예쁘게 보여주는 설정
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        # 화면에 보여줄 이름표
        labels = {
            'title': '상품명',
            'description': '상세설명',
            'image': '상품 이미지',
            'start_price': '시작 가격 (원)',
            'start_time': '경매 시작 시간',
            'end_time': '경매 종료 시간',
        }