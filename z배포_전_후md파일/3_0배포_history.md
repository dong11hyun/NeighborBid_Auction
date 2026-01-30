# NeighborBid Auction 서비스 배포 및 개발 내역 분석

현재 코드 베이스와 서버 구성을 바탕으로 분석한 **프로젝트 구현 및 배포 진행 순서**입니다.
질문하신 **"내가 SSL 인증서를 적용했나?"** 에 대한 답은 **"네, 적용되어 있습니다"** 입니다. (Nginx 설정과 Certbot 컨테이너가 증거입니다.)

## 1. 프로젝트 초기 구성 (Django Basic)
*   **Django 프로젝트 생성**: `config`, `users`, `auctions` 등 기본 앱 구조 생성.
*   **환경 변수 분리**: `.env` 파일을 사용하여 비밀 키(Secret Key)와 디버그 모드 관리 시작.

## 2. 데이터베이스 및 백엔드 고도화
*   **PostgreSQL 도입**:
    *   초기 `sqlite3`에서 프로덕션 레벨의 `PostgreSQL`로 데이터베이스 변경.
    *   `settings.py`의 `DATABASES` 설정이 `django.db.backends.postgresql`로 되어 있음.
*   **비동기 및 실시간 기능 (Channels & Redis)**:
    *   경매 입찰 등의 실시간 기능을 위해 `Django Channels`와 `Daphne` 서버 도입.
    *   이를 뒷받침하기 위한 **Redis** 캐시/메시지 브로커 설치 (`docker-compose`의 `redis` 서비스).

## 3. 컨테이너화 (Dockerization)
*   **Docker 도입**:
    *   `Dockerfile.prod` 작성을 통해 애플리케이션 실행 환경을 이미지로 만듦.
    *   `docker-compose.prod.yml`을 작성하여 Web, DB, Redis 등 여러 서비스를 한 번에 관리하는 구조 완성.

## 4. 웹 서버 및 리버스 프록시 구축 (Nginx)
*   **Nginx 도입**:
    *   Django(Daphne) 앞에 **Nginx**를 두어 정적 파일(Static/Media) 처리와 포트 포워딩을 담당하게 함.
    *   `nginx.conf`에서 80번 포트(HTTP) 요청을 처리하도록 설정.

## 5. 도메인 연결 및 SSL 보안 인증서 적용 (현재 단계)
*   **도메인 연결**: `neighborbid.com` 도메인을 구매하여 서버 IP와 연결.
*   **Certbot 도입 (SSL 인증서 발급)**:
    *   `docker-compose.prod.yml`에 `certbot` 컨테이너 추가.
    *   LetsEncrypt를 통해 무료 SSL 인증서를 자동 발급 및 갱신하도록 설정.
*   **HTTPS 설정 (Nginx)**:
    *   `nginx.conf`에 `listen 443 ssl;` 블록 추가.
    *   발급받은 인증서(`fullchain.pem`, `privkey.pem`)를 Nginx에 연동하여 보안 접속(HTTPS) 활성화.
    *   **이 과정에서 보안 수준이 올라가며 오늘 겪은 `CSRF` 문제가 발생.** (보안이 제대로 작동한다는 것. 개고생함)

## 6. 모니터링 및 추가 도구
*   **Metabase 도입**:
    *   데이터 시각화 및 분석을 위해 `metabase` 컨테이너 추가.
    *   DB와 연동하여 관리자 대시보드 구축 시도.

---

### **결론**
현재 사용자님의 서버는 단순히 코드를 올린 수준을 넘어, **HTTPS 보안 설정, DB/Redis 분리, 실시간 서버, 모니터링 도구**까지 갖춘 **완전한 프로덕션 아키텍처**를 갖추고 있습니다.

오늘 수정한 `CSRF_TRUSTED_ORIGINS`는 **5번 단계(SSL 적용)**가 완료되었기 때문에 필수로 따라오는 보안 설정 마무리 작업이었습니다.
