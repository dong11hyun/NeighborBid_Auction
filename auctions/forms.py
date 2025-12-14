# auctions/forms.py (새로 만들기)

from django import forms
from .models import Auction, Comment

# auctions/forms.py

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        # ▼▼▼ 'condition', 'shipping_payer' 필드 추가 ▼▼▼
        fields = ['title', 'description', 'category', 'condition', 'shipping_payer', 'image', 'start_price', 'instant_price', 'start_time', 'end_time']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '상품명을 입력하세요'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '상품에 대한 자세한 설명을 적어주세요.'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),       # 추가
            'shipping_payer': forms.Select(attrs={'class': 'form-select'}),  # 추가
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'start_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 100}),
            'instant_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 100}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        labels = {
            'title': '상품명',
            'description': '상세 설명',
            'category': '카테고리',
            'condition': '상품 상태',         # 라벨 추가
            'shipping_payer': '배송비 부담',  # 라벨 추가
            'image': '상품 이미지',
            'start_price': '시작 가격',
            'instant_price': '即 즉시 구매가 (선택)',
            'start_time': '경매 시작 시간',
            'end_time': '경매 종료 시간',
        }


# 맨 아래에 추가
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': '상품에 대해 궁금한 점을 남겨주세요.'
            }),
        }
        labels = {
            'content': '문의 내용'
        }