# 모니터링 시스템 구축 상세 가이드 (Metabase + Sentry + GA4)

운영자님, 결정해 주신 3가지 모니터링 도구를 위한 **코드 작업은 모두 완료**했습니다!
이제 각 서비스에 가입하고 **"키(Key)"**만 받아오면 됩니다.

아래 단계를 차근차근 따라와 주세요.

---

## 🚀 1. Metabase (비즈니스 대시보드) 실행하기

가입이 필요 없습니다. 이미 우리 서버에 설치해 두었습니다.

### 1-1. 서버에 적용
터미널에서 아래 명령어를 입력하여 Metabase를 실행합니다.
```bash
# 1. 변경된 설정 적용 및 실행
docker compose -f docker-compose.prod.yml up -d

# 2. 실행 확인 (neighborbid_metabase 컨테이너가 보여야 함)
docker compose -f docker-compose.prod.yml ps
```

### 1-2. 접속 및 초기 설정
1. 인터넷 브라우저 주소창에 `http://[서버_IP]:3000` 입력
2. **"Let's get started"** 클릭
3. 관리자 계정 생성 (이메일/비번 설정)
4. **"Add your data"** 단계에서 정보 입력:
   * **Database type**: `PostgreSQL`
   * **Name**: `NeighborBid DB` (아무거나)
   * **Host**: `postgres` (★중요: localhost 아님!)
   * **Port**: `5432`
   * **Database name**: `neighborbid` (env 파일의 DB_NAME)
   * **Username**: `postgres` (env 파일의 DB_USER)
   * **Password**: (env 파일의 DB_PASSWORD)
5. **"Finish"** 클릭 → 대시보드 생성 완료!

---

## 🚨 2. Sentry (에러 감지) 설정하기

### 2-1. 키 발급 (DSN)
1. [Sentry.io 회원가입](https://sentry.io/signup/) (무료 개발자 플랜)
2. **Create Project** 클릭 → **Django** 선택
3. "Configure SDK" 화면에서 **DSN** 이라고 적힌 URL을 복사합니다.
   * 예: `https://abcd123...@o456.ingest.sentry.io/789`

### 2-2. 서버에 키 등록
서버 터미널에서 `.env` 파일을 열고 복사한 키를 붙여넣습니다.

```bash
nano .env
```
(맨 아래 줄에 추가)
```env
# Sentry DSN
SENTRY_DSN=https://복사한_주소_전체
```
저장 후(`Ctrl+O`, Enter → `Ctrl+X`) 서버를 재시작합니다.
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## 🌐 3. Google Analytics 4 (방문자 분석)

### 3-1. 태그 발급
1. [Google Analytics](https://analytics.google.com/) 접속 및 '계정 만들기'
2. 속성 생성 후 **"웹"** 플랫폼 선택
3. 스트림 생성 완료 후 **"측정 ID (G-XXXXXXXXXX)"** 확인
4. **"Google 태그 보기"** → 코드 복사

### 3-2. 코드에 붙여넣기 (이건 직접 하셔야 합니다!)
프로젝트 폴더 내 `auctions/templates/auctions/base.html` 파일을 엽니다.
`<head>` 태그 바로 아래에 복사한 코드를 붙여넣으세요.

```html
<head>
    <!-- 여기에 구글 태그 붙여넣기 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX');
    </script>
    ...
</head>
```
그 후 `docker compose`를 다시 빌드해야 적용됩니다.
```bash
# HTML 수정 후 재배포
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 📊 4. 서버 트래픽 (네트워크 사용량) 확인법

이건 별도 설치 없이 **AWS Lightsail 콘솔**에서 바로 봅니다.

1. AWS Lightsail 콘솔 접속
2. 생성한 인스턴스 클릭 (NeighborBid)
3. **"지표(Metrics)"** 탭 클릭
4. 그래프 선택:
   * **NetworkIn**: 들어오는 트래픽 (사용자 업로드 등)
   * **NetworkOut**: 나가는 트래픽 (페이지 로딩, 이미지 전송 등) - **과금 기준**

> **Tip**: NetworkOut이 급증하면 사용자가 늘어난 것이니 기뻐하시면 됩니다! (월 3TB까지 무료니 안심하세요)
