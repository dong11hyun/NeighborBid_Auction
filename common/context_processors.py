from django.conf import settings

def global_settings(request):
    """
    모든 템플릿에서 공통으로 사용할 변수를 반환합니다.
    (예: Google Maps API Key, 사이트 이름 등)
    """
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'GA4_MEASUREMENT_ID': getattr(settings, 'GA4_MEASUREMENT_ID', None),
    }
