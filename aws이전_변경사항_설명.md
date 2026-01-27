# NeighborBid 확장성 및 안정성 업데이트 보고서

> **"로컬 데모 수준에서 실제 서비스 가능한 수준으로의 도약"**
> 확장성과 데이터 무결성을 보장하기 위한 핵심 로직 리팩토링 및 보안 강화 작업

**작업 기간**: 2026.01.27 ~ 현재
**상태**: PostgreSQL 전환 준비 완료 (코드 리팩토링 100% 완료)

---

## 🤔 변경의 이유 (Why?)

#### 1. 데이터 무결성이 깨져있음 (Critical)
- **문제**: 돈이 오가는 경매 시스템인데, 입찰 도중 다른 사람이 입찰하면 잔액이 꼬이는 **동시성 문제(Race Condition)**가 발생할 수 있었습니다.
- **버그**: 낙찰자를 저장할 곳(`winner` 필드)이 없어서 즉시 구매(`buy_now`) 시 에러가 발생했습니다.

#### 2. 보안 취약점 (Security)
- DB 비밀번호와 `SECRET_KEY`가 코드에 그대로 노출되어 있어, 깃허브 등에 올리면 해킹 위험이 컸습니다.

#### 3. 성능 이슈 (N+1 Query)
- 경매 목록을 볼 때마다 판매자 정보, 카테고리 정보를 매번 다시 조회하여, 경매 글이 100개면 DB 조회가 300번 일어나는 비효율이 있었습니다.

---

## 🧐 상세 변경 내역 (Code Deep Dive)

아래 파일들은 위 문제들을 해결하기 위해 수정되었습니다.

### 1. `auctions/models.py`: 낙찰자 필드 추가 [✅ 버그 해결]

**수정 이유**:
`확장성.md` 분석 결과, 경매가 종료되었을 때 **누가 낙찰받았는지 저장하는 필드가 누락**되어 있었습니다. 이로 인해 즉시 구매 기능을 실행하면 "winner 필드가 없다"는 **AttributeError**가 발생했습니다.

**변경된 코드 예시**:
```python
class Auction(models.Model):
    # ... (기존 필드)
    # [NEW] 낙찰자 (경매 종료 시 확정) - 이 필드가 없어서 로직이 터지고 있었음
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='won_auctions',
        verbose_name="낙찰자"
    )
    # [NEW] 이미지 확장자 검증 (보안) - exe 파일 등을 올리는 것 방지
    image = models.ImageField(..., validators=[FileExtensionValidator(...)])
```

---

### 2. `auctions/services.py`: 핵심 비즈니스 로직 [✅ 데이터 무결성]

**수정 이유 (가장 중요)**:
돈을 다루는 핵심 로직입니다. 3가지 치명적인 문제가 있었습니다.
1.  **부동소수점 오차**: 파이썬 `float`로 돈 계산 시 100원이 99.999999원이 될 수 있음 -> **`Decimal` 도입**
2.  **동시성 문제**: A와 B가 동시에 입찰하면 둘 다 돈이 빠져나가거나 한 명만 적용되는 문제 -> **`select_for_update` (DB Lock) 도입**
3.  **알림 누락**: 입찰해도 판매자나 이전 입찰자에게 알림이 안 감 -> **`Notification` 연동**

**변경된 코드 예시**:
```python
def place_bid(auction_id, user, amount):
    with transaction.atomic(): # 트랜잭션 시작 (중간에 에러나면 전체 롤백)
        # [Lock] 내가 조회하고 수정하는 동안 남들은 건들지 마!
        auction = Auction.objects.select_for_update().get(id=auction_id)
        
        # [Decimal] 정확한 돈 계산
        decimal_amount = Decimal(str(amount))
        
        # [Notification] 이전 1등에게 "너 상위 입찰 당했어" 알림
        if last_bid:
             transaction.on_commit(send_outbid_notification) # 트랜잭션 성공 후 발송
```

---

### 3. `auctions/views.py`: 뷰 최적화 및 방어 로직 [✅ 성능/안전]

**수정 이유**:
1.  **N+1 문제(성능)**: 경매 리스트 조회 시 엄청난 수의 DB 쿼리가 발생하던 것을 **1번의 쿼리로 최적화**했습니다.
2.  **입력값 검증(안전)**: 사용자가 입찰 금액에 `-1000`이나 `문자열`을 넣으면 서버가 죽거나 잔액이 복사되는() 버그를 막았습니다.

**성능 개선 결과**:
```python
# [BEFORE] 경매 100개 조회 시 -> 쿼리 101번 발생 (느림)
auctions = Auction.objects.filter(...)

# [AFTER] 경매 100개 조회 시 -> 쿼리 1번 발생 (빠름)
auctions = Auction.objects.filter(...).select_related('seller', 'category')
```

---

### 4. `users/views.py`: 리뷰 권한 체크 [✅ 로직 보완]

**수정 이유**:
기존에는 "마지막 입찰자"를 낙찰자로 간주했습니다. 그런데 "즉시 구매"를 한 사람은 입찰 기록 없이 바로 `winner`가 되므로, **즉시 구매자는 리뷰를 못 쓰는 황당한 버그**가 있었습니다.
-> 이제 `winner` 필드를 확인하므로 즉시 구매자도 정상적으로 리뷰를 쓸 수 있습니다.

---

### 5. `config/settings.py` & `.env`: 보안 설정 [✅ 보안]

**수정 이유**:
소스코드에 `SECRET_KEY = 'django-insecure-...'`라고 적혀 있었습니다. 이 코드가 유출되면 해커가 관리자 권한을 탈취할 수 있습니다.
-> **환경 변수(.env)** 파일로 비밀키를 숨기고, 코드에서는 `os.environ.get()`으로 불러오도록 변경했습니다.

---

### 6. `config/celery.py` & `auctions/tasks.py`: 자동화 [✅ 확장성]

**수정 이유**:
경매 종료 시간이 새벽 3시라면? 기존에는 관리자가 깨어서 버튼을 눌러야 종료되었습니다.
-> **Celery(비동기 작업 큐)**를 도입하여, 1분마다 종료된 경매를 찾아 자동으로 낙찰 처리하는 코드를 준비했습니다.

---

## 🚀 결론 및 다음 단계

이제 "돌아만 가는 코드"에서 **"안전하고 확장 가능한 코드"**로 변경되었습니다.
하지만 아직 데이터베이스가 SQLite(파일 기반)라서, 동시 접속자가 많아지면 파일 락(Lock) 때문에 느려집니다.

**Next Step**:
- 코드는 준비되었으니, 이제 **PostgreSQL(전문 DB)**로 교체하여 실제 대용량 트래픽을 감당할 수 있게 해야 합니다.

---

### 7. 추가 설명: Celery와 환경변수 동작 원리

#### `config/celery.py` 동작 원리
이 파일은 Django와 Celery(비동기 작업 큐)를 연결하는 진입점입니다.
1. **`os.environ.setdefault`**: Celery가 Django 설정(`config/settings.py`)을 알 수 있도록 환경 변수를 설정합니다.
2. **`app = Celery(...)`**: Celery 앱 인스턴스를 생성하여 전체 작업을 관리합니다.
3. **`app.config_from_object`**: Django의 `settings.py`에서 `CELERY_`로 시작하는 설정들을 가져와 적용합니다.
4. **`app.autodiscover_tasks()`**: 각 앱(예: `auctions`) 폴더에 있는 `tasks.py` 파일을 자동으로 찾아 작업 목록에 등록합니다.

#### `auctions/tasks.py` 동작 원리
실제로 백그라운드에서 주기적으로 실행될 작업(함수)을 정의하는 곳입니다.
- **`@shared_task`**: 이 데코레이터가 붙은 함수는 Celery가 실행 가능한 '작업(Task)'으로 인식합니다.
- **`check_expired_auctions`**: 이 함수는 설정된 주기(예: 1분)마다 호출되어, 종료 시간이 지났지만 상태가 활성(ACTIVE)인 경매를 찾아 **자동으로 낙찰 처리(`determine_winner`)**를 수행합니다. 이를 통해 관리자가 일일이 종료 버튼을 누르지 않아도 됩니다.

#### `.env` 환경변수 동작 원리
보안이 필요한 정보(비밀번호, API 키)나 개발/운영 환경별로 달라지는 설정을 코드와 분리하여 관리하는 방식입니다.
1. **작성 (`.env`)**: 파일 내부에 `SECRET_KEY=...` 처럼 `키=값` 형태로 저장합니다. 이 파일은 `.gitignore`에 등록되어 깃허브 등에 올라가지 않습니다.
2. **로드 (`settings.py`)**: `load_dotenv()` 함수가 실행되면 `.env` 파일의 내용을 읽어 시스템의 환경변수(`os.environ`)로 불러옵니다.
3. **사용**: 코드 내에서 `os.environ.get('KEY')`를 통해 값을 안전하게 가져다 씁니다.

#### [PostgreSQL 전용 설정]

> Environment Parity (환경 일치): 개발은 SQLite, 운영은 PostgreSQL을 쓰면, 특정 함수(예: 날짜 계산, JSON 필드 등)가 다르게 동작해서 예기치 못한 버그가 터질 수 있습니다. 그래서 **"개발과 운영 환경을 최대한 똑같이 맞추는 것"**이 모던 웹 개발의 정석(12-Factor App)입니다.

> if/else를 쓰는 경우: 아주 초기 스타트업이거나, 도커를 띄우기 힘든 열악한 로컬 환경일 때 편의상 쓰기도 하지만, 웬만하면 지금처럼 Docker로 통일하는 것이 훨씬 프로페셔널한 방식입니다.

---

### 8. FAQ: DB 버전과 접속 방법

> ports: "호스트포트:컨테이너포트"

>내 컴퓨터(호스트)의 5433번 포트로 들어온 요청을
>컨테이너 내부의 5432번 포트로 전달한다

#### Q1. 왜 Postgres 15-alpine을 쓰나요? 내 로컬은 18인데?
- **AWS 등 호환성**: 클라우드(AWS RDS)에서 가장 안정적으로 지원하는 'Long Term Support (LTS)' 성격의 버전이 15~16 버전대입니다. 최신 버전(18)은 AWS에서 아직 지원하지 않거나 불안정할 수 있어, 배포 시 버전을 낮춰야 하는 번거로움이 있을 수 있습니다.
- **Alpine 리눅스**: `alpine`은 용량이 매우 작아(5MB~), 배포 속도가 빠르고 보안 공격 표면이 적어 실무에서 선호합니다.
- **호환성 영향**: Django ORM을 사용하신다면 15와 18 사이의 차이는 거의 **없습니다**. 특수한 최신 SQL 문법을 직접 쓰지 않는 한 100% 호환됩니다.
```
**지금 시점에선 18은 별로가 아니라 “아직 대상이 아님”**이야 🙂

왜 PostgreSQL 18이 애매하냐면

PostgreSQL 18은 아직 정식 릴리스가 안 됐어
→ 현재는 개발 브랜치 / 베타·RC 단계(있다면) 수준

AWS RDS / Aurora에서 공식 지원 ❌
→ AWS는 정식 메이저 릴리스 + 충분한 검증 후에야 지원함

프로덕션에서 쓰면:

확장(extension) 호환성 불확실

ORM / 드라이버 이슈 가능

AWS 장애 대응·패치 혜택 없음

그래서 **“별로”라기보단 “아직 쓰면 안 되는 카드”**에 가까워.
```

#### Q2. 로컬 DB 툴(DBeaver, pgAdmin)로 도커 DB에 어떻게 붙나요? (포트 충돌 해결)
로컬에 이미 PostgreSQL(18 등)이 설치되어 있다면 5432 포트가 충돌납니다.
따라서 **도커 DB를 5433 포트**로 열어서 접속하는 방법을 사용합니다.

**1. 설정 적용 (터미널)**
`docker-compose.yml` 파일에서 포트를 `5433:5432`로 변경했습니다. 아래 명령어로 적용해주세요.
```bash
docker compose up -d
```

**2. 연결 설정 (DBeaver / pgAdmin)**
*   **Host**: `localhost`
*   **Port**: `5433` (5432 아님!)
*   **Database**: `neighborbid`
*   **Username**: `postgres`
*   **Password**: `password`

이렇게 하면 로컬에 깔린 Postgres는 건드리지 않고, 도커 안의 Postgres(15)에 안전하게 접속할 수 있습니다.

#### Q3. 왜 도커 DB를 쓰는데 로컬 DB 툴로 붙나요?
- 도커는 **실행 환경(서버)**이고, DBeaver/pgAdmin은 **관리 도구(클라이언트)**입니다.
- 도커 컨테이너가 5432 포트를 열어주었기 때문에, 내 컴퓨터(Host)에 설치된 도구로 도커 내부의 DB에 접속해서 데이터를 확인하고 쿼리를 날릴 수 있습니다. 이것이 도커를 쓰는 큰 장점 중 하나입니다.


