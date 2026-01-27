# 구현 계획 - 확장성 및 안정성 개선 설계도

`확장성.md`에 기술된 내용을 바탕으로 NeighborBid 프로젝트의 코드를 개선하기 위한 계획입니다. PostgreSQL 전환 전에 코드 레벨의 문제점들을 먼저 수정합니다.

## 목표
`확장성.md`에서 지적된 버그 수정, 보안 취약점 보완, 구조적 개선을 통해 실제 AWS 런칭이 가능한 수준으로 안정화합니다.

## 검토 필요 사항
> [!IMPORTANT]
> **데이터베이스 변경**: `Auction` 모델에 `winner` 필드가 추가되므로 `makemigrations` 및 `migrate` 실행이 필요합니다.
> **환경 변수**: 보안 설정을 위해 `.env` 파일이 도입됩니다. 로컬 개발용 기본 `.env` 파일을 생성할 예정입니다.

## 변경 제안 내용

### 1. 치명적 버그 및 로직 수정
#### [MODIFY] [auctions/models.py](file:///c:/NeighborBid_Auction/auctions/models.py)
- `Auction` 모델에 `winner` (낙찰자) 필드 추가 (ForeignKey).

#### [MODIFY] [auctions/services.py](file:///c:/NeighborBid_Auction/auctions/services.py)
- **Bug #1 & #4**: `buy_now` 함수 수정 (`winner` 필드 사용, `on_commit` 클로저 변수 캡처 문제 해결).
- **Incomplete #2**: `place_bid` 함수에 알림(Notification) 생성 로직 추가.
- **Incomplete #3**: 입찰 시 `bid_unit`(입찰 단위) 배수 검증 로직 추가.
- **Warning #6**: 지갑 잔액 연산 시 명시적 `Decimal` 타입 변환 적용.

#### [MODIFY] [auctions/views.py](file:///c:/NeighborBid_Auction/auctions/views.py)
- **Bug #2**: `charge_wallet` 함수에 `transaction.atomic()` 및 검증 로직 추가.
- **Bug #3**: `auction_detail` 입찰 처리 시 `amount` 값 유효성 검증 강화.
- **Critical #4**: `auction_list` 조회 시 `select_related`/`prefetch_related` 사용하여 N+1 문제 해결.

#### [MODIFY] [users/views.py](file:///c:/NeighborBid_Auction/users/views.py)
- **Incomplete #4**: `create_review` 함수에서 `auction.winner` 필드를 확인하도록 수정.

### 2. 보안 및 설정 강화
#### [NEW] [.env](file:///c:/NeighborBid_Auction/.env)
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` 등 민감 정보를 관리하기 위한 파일 생성.

#### [MODIFY] [config/settings.py](file:///c:/NeighborBid_Auction/config/settings.py)
- **Security #1-4**: 환경 변수(`os.environ`)에서 설정값을 읽어오도록 수정.
- **Security #5**: 배포 환경을 위한 보안 헤더 설정 추가 (HSTS, XSS 방지 등).
- **Critical #2**: 세션 저장소를 DB에서 Redis로 변경.

#### [NEW] [config/custom_middleware.py](file:///c:/NeighborBid_Auction/config/custom_middleware.py)
- **Security #6**: 웹소켓 접속 시 권한을 확인하는 `AuctionAccessMiddleware` 추가.

#### [MODIFY] [config/asgi.py](file:///c:/NeighborBid_Auction/config/asgi.py)
- 웹소켓 라우팅에 커스텀 미들웨어 적용.

#### [MODIFY] [auctions/models.py](file:///c:/NeighborBid_Auction/auctions/models.py)
- **Warning #5**: 상품 이미지 업로드 시 파일 크기 및 확장자 검증기(`validator`) 추가.

### 3. 구조적 개선 및 미완성 로직
#### [NEW] [config/celery.py](file:///c:/NeighborBid_Auction/config/celery.py) 및 [auctions/tasks.py](file:///c:/NeighborBid_Auction/auctions/tasks.py)
- **Incomplete #1**: Celery 설정 추가 및 경매 자동 종료(`check_expired_auctions`) 태스크 코드 작성.

#### [MODIFY] [auctions/consumers.py](file:///c:/NeighborBid_Auction/auctions/consumers.py)
- **Critical #3**: 연결 종료(`disconnect`) 시 명시적 로깅 추가.

## 검증 계획

### 자동화 테스트
- 기존 테스트 코드를 실행하여 회귀 테스트 진행: `python manage.py test auctions`

### 수동 검증 항목
1.  **환경 설정**: `.env` 파일 생성 및 적용 확인.
2.  **마이그레이션**: `python manage.py makemigrations` -> `python manage.py migrate` 성공 여부 확인.
3.  **서버 실행**: `daphne`로 서버 구동 확인.
4.  **주요 기능 테스트**:
    *   **로그인/세션**: Redis 세션 작동 확인.
    *   **지갑 충전**: 트랜잭션 기록 및 잔액 변경 확인.
    *   **경매 생성/입찰**: 유효성 검사 및 정밀도(Decimal) 확인, 알림 생성 확인.
    *   **즉시 구매**: `winner` 필드 업데이트, 트랜잭션 로그, 종료 알림 확인.
    *   **후기 작성**: 낙찰자 권한 체크 확인.
