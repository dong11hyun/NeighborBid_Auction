# Let it Snow ❄️ 구현 완료

## 생성/수정된 파일

| 파일 | 변경 내용 |
|------|-----------|
| [snow.js](file:///c:/NeighborBid_Auction/static/js/snow.js) | Canvas 기반 눈 애니메이션 + LocalStorage 설정 저장 |
| [snow.css](file:///c:/NeighborBid_Auction/static/css/snow.css) | 토글 버튼 스타일 (우측 하단 고정, 그라데이션 애니메이션) |
| [base.html](file:///c:/NeighborBid_Auction/auctions/templates/auctions/base.html) | `{% load static %}`, CSS/JS 링크, ❄️ 토글 버튼 추가 |
| [nginx.conf](file:///c:/NeighborBid_Auction/nginx.conf) | HTTP 80 포트에도 `/static/`, `/media/` 경로 추가 |

---

## 서버 배포 방법

```bash
# 1. 프로젝트 디렉토리로 이동
cd /path/to/NeighborBid_Auction

# 2. Git에서 최신 변경사항 가져오기
git pull origin main

# 3. Docker 컨테이너 재빌드 및 재시작
docker-compose -f docker-compose.prod.yml build web
docker-compose -f docker-compose.prod.yml up -d web nginx
```

> [!IMPORTANT]
> `docker-compose build`가 `collectstatic`을 자동 실행하므로 별도 명령 불필요

---

## 사용 방법

1. 웹사이트 접속 후 **우측 하단의 ❄️ 버튼** 클릭
2. 눈이 내리기 시작 (버튼이 녹색으로 변경)
3. 다시 클릭하면 눈 효과 OFF
4. **설정은 LocalStorage에 저장** → 페이지 새로고침해도 유지됨

---

## 기술 구현

- **Canvas API**: 150개 눈송이 파티클을 60fps로 렌더링
- **각 눈송이**: 랜덤 크기, 속도, 바람(좌우 흔들림), 투명도
- **LocalStorage**: `snowEnabled` 키로 on/off 상태 저장
- **pointer-events: none**: 눈 위에서도 웹사이트 클릭 가능

---
---

# 눈 내리는 효과 (Let it Snow) 구현

Google AI Studio의 "Let it snow" 이스터에그처럼 웹사이트에 눈 내리는 애니메이션을 추가합니다. 토글 버튼(on/off)으로 사용자가 효과를 켜고 끌 수 있습니다.

## 기술적 접근 방식

눈 효과는 순수 JavaScript + CSS로 구현합니다:
- **Canvas API** 또는 **DOM 기반 파티클**을 사용하여 눈송이 애니메이션
- **LocalStorage**를 이용해 사용자의 on/off 설정 저장
- 페이지 새로고침 후에도 설정 유지

---

## Proposed Changes

### Static Files (신규 생성)

#### [NEW] [snow.js](file:///c:/NeighborBid_Auction/auctions/static/js/snow.js)

눈 내리는 효과를 담당하는 JavaScript 파일:
- Canvas를 생성하여 화면 전체에 오버레이
- 눈송이 파티클 생성 및 애니메이션 루프
- `startSnow()`, `stopSnow()`, `toggleSnow()` 함수 제공
- LocalStorage에 설정 저장/불러오기

#### [NEW] [snow.css](file:///c:/NeighborBid_Auction/auctions/static/css/snow.css)

눈 효과 관련 스타일:
- Canvas 오버레이 스타일 (전체화면, pointer-events: none)
- 토글 버튼 스타일

---

### Templates

#### [MODIFY] [base.html](file:///c:/NeighborBid_Auction/auctions/templates/auctions/base.html)

변경 사항:
1. `{% load static %}` 태그 추가
2. `snow.css` 링크 추가
3. 눈 효과 토글 버튼 추가 (navbar 또는 footer에 ❄️ 아이콘)
4. `snow.js` 스크립트 추가
5. 페이지 로드 시 LocalStorage 설정에 따라 눈 효과 시작

---

### Settings

#### [MODIFY] [settings.py](file:///c:/NeighborBid_Auction/config/settings.py)

`STATICFILES_DIRS` 설정 확인/추가 (auctions/static 경로 포함)

---

## Verification Plan

### 수동 테스트

1. **Django 개발 서버 실행**
   ```bash
   cd c:\NeighborBid_Auction
   python manage.py runserver
   ```

2. **브라우저에서 확인** (http://127.0.0.1:8000/)
   - ❄️ 버튼이 화면에 표시되는지 확인
   - 버튼 클릭 시 눈이 내리기 시작하는지 확인
   - 다시 클릭 시 눈이 멈추는지 확인
   - 페이지 새로고침 후 설정이 유지되는지 확인 (LocalStorage)

3. **콘솔 에러 확인**
   - 브라우저 개발자 도구(F12)에서 JavaScript 에러 없는지 확인
