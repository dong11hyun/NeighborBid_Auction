# NeighborBid 웹 런칭 완벽 가이드

> **목표**: 서버 기초 개념부터 AWS를 이용한 실제 런칭까지 완벽 정리
> **대상**: 처음 웹사이트를 런칭하는 개발자

---

## 📚 목차

| 번호 | 내용 |
|:---:|------|
| 1 | [VPS란 무엇인가?](#1-vps란-무엇인가) |
| 2 | [AWS 초보자 적합성 분석](#2-aws-초보자-적합성-분석) |
| 3 | [AWS 비용 분석](#3-aws-비용-분석) |
| 4 | [서버 기초 지식](#4-서버-기초-지식) |
| 5 | [NeighborBid 최적 서버 추천](#5-neighborbid-최적-서버-추천) |
| 6 | [AWS Lightsail 단계별 런칭 가이드](#6-aws-lightsail-단계별-런칭-가이드) |

---

# 1. VPS란 무엇인가?

## 1.1 VPS 정의

**VPS (Virtual Private Server, 가상 사설 서버)**

```
┌─────────────────────────────────────────────────────────────┐
│                    물리적 서버 (실제 컴퓨터)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   VPS #1    │  │   VPS #2    │  │   VPS #3    │  ...     │
│  │  (당신의     │  │  (다른       │  │  (또 다른     │          │
│  │   서버)      │  │   고객)      │  │   고객)      │          │
│  │             │  │             │  │             │          │
│  │ CPU: 1코어  │  │ CPU: 2코어  │  │ CPU: 4코어  │          │
│  │ RAM: 1GB    │  │ RAM: 2GB    │  │ RAM: 8GB    │          │
│  │ SSD: 25GB   │  │ SSD: 50GB   │  │ SSD: 160GB  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                    ▲ 가상화 기술로 분리 ▲                      │
└─────────────────────────────────────────────────────────────┘
```

**쉬운 비유**: 아파트 한 동(물리 서버)에서 각자의 집(VPS)을 빌려 사용하는 것

## 1.2 호스팅 유형 비교

| 유형 | 설명 | 비용 | 자유도 | 예시 |
|-----|-----|-----|-------|-----|
| **공유 호스팅** | 하나의 서버를 여러 사이트가 공유 | 월 $1~5 | 낮음 | 카페24, 닷홈 |
| **VPS** | 가상 서버 독점 사용 | 월 $5~50 | 높음 | AWS, DigitalOcean |
| **전용 서버** | 물리 서버 전체 독점 | 월 $100+ | 최고 | 대기업용 |

## 1.3 VPS를 선택해야 하는 이유

NeighborBid 프로젝트에 VPS가 필요한 이유:

| 요구사항 | VPS 필요 이유 |
|---------|-------------|
| **Docker 실행** | 공유 호스팅에서는 Docker 사용 불가 |
| **WebSocket** | 실시간 통신을 위한 포트 제어 필요 |
| **Redis** | 백그라운드 서비스 실행 권한 필요 |
| **PostgreSQL** | 데이터베이스 서버 직접 운영 |

---

# 2. AWS 초보자 적합성 분석

## 2.1 AWS란?

**AWS (Amazon Web Services)**: 아마존이 제공하는 클라우드 컴퓨팅 플랫폼

## 2.2 AWS 서비스 종류 (초보자용 정리)

| 서비스 | 용도 | 초보자 난이도 | 권장 |
|-------|-----|:-----------:|:---:|
| **EC2** | 가상 서버 (VPS) | ⭐⭐⭐⭐⭐ 어려움 | ❌ |
| **Lightsail** | 간편 VPS | ⭐⭐ 쉬움 | ✅ 강력 추천 |
| **Elastic Beanstalk** | 자동 배포 | ⭐⭐⭐ 보통 | ⚠️ |
| **RDS** | 관리형 DB | ⭐⭐⭐ 보통 | 선택적 |
| **ECS/Fargate** | 컨테이너 | ⭐⭐⭐⭐ 어려움 | ❌ |

## 2.3 초보자 적합성 판정

### ✅ AWS Lightsail - 초보자에게 최적

| 장점 | 설명 |
|-----|------|
| **간편한 UI** | EC2보다 훨씬 직관적인 대시보드 |
| **고정 요금제** | 예측 가능한 월 정액 비용 |
| **원클릭 설치** | Docker, WordPress 등 프리셋 제공 |
| **한국 리전** | 서울 리전 지원 (ap-northeast-2) |
| **무료 체험** | 첫 3개월 무료 (가장 저렴한 플랜) |

### ❌ EC2 - 초보자에게 비추천

| 단점 | 설명 |
|-----|------|
| **복잡한 설정** | VPC, 보안 그룹, IAM 등 설정 필요 |
| **변동 요금** | 사용량 기반으로 예상 비용 어려움 |
| **학습 곡선** | 제대로 사용하려면 수주 학습 필요 |

> [!TIP]
> **결론**: 처음 런칭은 **AWS Lightsail**로 시작하고, 트래픽이 늘면 EC2로 마이그레이션하세요.

---

# 3. AWS 비용 분석

## 3.1 AWS Lightsail 요금표 (2026년 기준, 서울 리전)

| 플랜 | RAM | CPU | SSD | 전송량 | 월 비용 | 원화 환산 |
|-----|-----|-----|-----|-------|--------|----------|
| **$5** | 1GB | 1코어 | 40GB | 2TB | $5 | 약 6,500원 |
| **$10** ⭐추천 | 2GB | 1코어 | 60GB | 3TB | $10 | 약 13,000원 |
| **$20** | 4GB | 2코어 | 80GB | 4TB | $20 | 약 26,000원 |
| **$40** | 8GB | 2코어 | 160GB | 5TB | $40 | 약 52,000원 |

## 3.2 NeighborBid 프로젝트 비용 계산

### 최소 권장 사양: **$10 플랜**

```
서비스별 메모리 사용량 (추정):
├── Django + Daphne: 200~400MB
├── PostgreSQL: 300~500MB  
├── Redis: 50~100MB
├── Nginx: 10~50MB
└── 시스템 예약: 300MB
────────────────────────────
총합: 약 1.2GB ~ 1.5GB 필요
→ 최소 2GB RAM 플랜 권장
```

### 월간 총 예상 비용

| 항목 | 비용 | 비고 |
|-----|-----|------|
| Lightsail $10 플랜 | 13,000원 | 서버 비용 |
| 도메인 (.com) | 1,500원/월 | 연간 약 18,000원 |
| SSL 인증서 | 0원 | Let's Encrypt 무료 |
| **월 합계** | **약 14,500원** | |

## 3.3 무료 체험

| 플랫폼 | 무료 기간 | 조건 |
|-------|----------|------|
| **AWS Lightsail** | 첫 3개월 무료 | $5 플랜 한정 |
| **AWS 프리 티어** | 12개월 | EC2 t2.micro, RDS 등 |

> [!IMPORTANT]
> AWS Lightsail $5 플랜은 **첫 3개월 무료**입니다!
> 단, RAM 1GB는 부족할 수 있으니 테스트 후 $10으로 업그레이드 권장.

---

# 4. 서버 기초 지식

## 4.1 알아야 할 핵심 개념

### SSH (Secure Shell)

```bash
# 원격 서버에 접속하는 명령어
ssh -i "my-key.pem" ubuntu@123.456.789.10
```

- 서버에 원격으로 접속하는 방법
- 비밀번호 대신 **키 파일(.pem)** 사용 권장

### 포트 (Port)

```
┌─────────────────────────────┐
│        서버 (VPS)            │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │:22  │ │:80  │ │:443 │   │
│  │SSH  │ │HTTP │ │HTTPS│   │
│  └──┬──┘ └──┬──┘ └──┬──┘   │
└─────┼───────┼───────┼───────┘
      ▼       ▼       ▼
   관리자   웹 접속(일반) 웹 접속(보안)
```

| 포트 | 용도 | 설명 |
|-----|-----|------|
| **22** | SSH | 서버 관리용 접속 |
| **80** | HTTP | 일반 웹 접속 |
| **443** | HTTPS | 암호화된 웹 접속 |
| **5432** | PostgreSQL | DB 접속 (외부 차단 권장) |
| **6379** | Redis | 캐시 서버 (외부 차단 권장) |

### IP 주소와 도메인

```
[사용자] → neighborbid.com → DNS → 123.456.789.10 → [서버]
```

- **IP 주소**: 서버의 실제 주소 (예: 123.456.789.10)
- **도메인**: 사람이 기억하기 쉬운 이름 (예: neighborbid.com)
- **DNS**: 도메인 → IP 변환 서비스

### 방화벽

```bash
# 특정 포트만 열어두는 설정
80 (HTTP)    → 열림 ✅
443 (HTTPS)  → 열림 ✅
22 (SSH)     → 열림 ✅ (관리자 IP만)
5432 (DB)    → 닫힘 ❌ (보안)
```

## 4.2 리눅스 기본 명령어

서버는 대부분 **Ubuntu Linux**를 사용합니다:

| 명령어 | 설명 | 예시 |
|-------|------|-----|
| `pwd` | 현재 위치 확인 | `pwd` → `/home/ubuntu` |
| `ls` | 파일 목록 | `ls -la` |
| `cd` | 폴더 이동 | `cd /var/www` |
| `mkdir` | 폴더 생성 | `mkdir myapp` |
| `nano` | 텍스트 편집 | `nano docker-compose.yml` |
| `sudo` | 관리자 권한 실행 | `sudo apt update` |

## 4.3 Docker 기본 개념

```
┌────────────────────────────────────────────────┐
│                 Docker Compose                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Django  │  │ Redis   │  │PostgreSQL│        │
│  │Container│  │Container│  │Container│         │
│  └─────────┘  └─────────┘  └─────────┘        │
│       ↑            ↑            ↑              │
│       └────────────┴────────────┘              │
│              내부 네트워크 연결                  │
└────────────────────────────────────────────────┘
```

| 개념 | 설명 |
|-----|------|
| **이미지** | 실행에 필요한 모든 것을 담은 패키지 |
| **컨테이너** | 이미지를 실행한 상태 (실제로 동작 중) |
| **Docker Compose** | 여러 컨테이너를 한 번에 실행 |

---

# 5. NeighborBid 최적 서버 추천

## 5.1 요구사항 분석

| 요구사항 | 필요 기술 | 서버 요건 |
|---------|----------|----------|
| Django 웹 서버 | Python 3.11+ | 1코어 CPU, 512MB+ RAM |
| 실시간 입찰 | Channels + Daphne | WebSocket 지원 |
| 사용자 세션 | Redis | 50~100MB RAM |
| 데이터 저장 | PostgreSQL | 300~500MB RAM |
| HTTPS | Nginx + Let's Encrypt | 포트 80, 443 개방 |

## 5.2 추천 서버 비교

| 순위 | 서비스 | 비용 | 장점 | 단점 | 추천도 |
|:---:|-------|-----|-----|------|:-----:|
| 🥇 | **AWS Lightsail** | $10/월 | AWS 생태계, 서울 리전, 무료 체험 | 고급 설정 제한 | ⭐⭐⭐⭐⭐ |
| 🥈 | **DigitalOcean** | $12/월 | 우수한 문서, 간편한 UI | 서울 리전 없음 | ⭐⭐⭐⭐ |
| 🥉 | **Vultr** | $10/월 | 서울 리전, 저렴 | 문서 부족 | ⭐⭐⭐ |

## 5.3 최종 추천: AWS Lightsail $10 플랜

```
선택 이유:
✅ 서울 리전 지원 (한국 사용자 빠른 응답)
✅ 3개월 무료 체험 가능
✅ Docker 사용 가능
✅ AWS 생태계 (추후 확장 용이)
✅ 고정 월 비용 (예측 가능)
✅ 간편한 관리 대시보드
```

---

# 6. AWS Lightsail 단계별 런칭 가이드

## 📋 전체 흐름

```
[1] AWS 계정 생성
      ↓
[2] Lightsail 인스턴스 생성
      ↓
[3] SSH 접속 설정
      ↓
[4] Docker 설치
      ↓
[5] 프로젝트 업로드
      ↓
[6] docker-compose 실행
      ↓
[7] 도메인 연결
      ↓
[8] SSL 인증서 설치
      ↓
[9] 🎉 런칭 완료!
```

---

## Step 1: AWS 계정 생성

1. [AWS 홈페이지](https://aws.amazon.com/ko/) 접속
2. **"무료로 시작하기"** 클릭
3. 이메일, 비밀번호 입력
4. **결제 정보 입력** (신용카드 필수, 실제 청구는 무료 기간 이후)
5. 휴대폰 인증 완료

> [!CAUTION]
> 신용카드 등록이 필요하지만, Lightsail $5 플랜은 **3개월 무료**입니다.
> 무료 기간 후 자동 청구되니 알림 설정을 권장합니다.

---

## Step 2: Lightsail 인스턴스 생성

### 2.1 Lightsail 콘솔 접속

1. AWS 콘솔에서 검색: **"Lightsail"**
2. **"인스턴스 생성"** 클릭

### 2.2 인스턴스 설정

```
[인스턴스 위치]
→ 서울 (ap-northeast-2a) 선택

[플랫폼 선택]
→ Linux/Unix 선택

[블루프린트 선택]
→ "OS 전용" → "Ubuntu 22.04 LTS" 선택

[인스턴스 플랜]
→ $10 USD (2GB RAM, 1vCPU, 60GB SSD) 선택

[인스턴스 이름]
→ "NeighborBid-Production" 입력

[생성] 버튼 클릭
```

### 2.3 고정 IP 할당

1. 인스턴스 클릭 → **"네트워킹"** 탭
2. **"정적 IP 생성"** 클릭
3. 이름: `NeighborBid-IP`
4. **"생성 및 연결"** 클릭

기록해두세요: `고정 IP: ___.___.___.___ `

### 2.4 포트 개방

**네트워킹** 탭에서 방화벽 규칙 추가:

| 포트 | 프로토콜 | 용도 |
|-----|---------|------|
| 22 | TCP | SSH (기본 열림) |
| 80 | TCP | HTTP (기본 열림) |
| 443 | TCP | HTTPS (추가 필요) |

---

## Step 3: SSH 접속 설정

### 3.1 브라우저에서 바로 접속 (가장 쉬움)

1. Lightsail 콘솔에서 인스턴스 클릭
2. **"SSH를 사용하여 연결"** 버튼 클릭
3. 브라우저에서 터미널 열림!

### 3.2 로컬 터미널에서 접속 (권장)

**Windows 사용자 (PowerShell 또는 WSL):**

```powershell
# 1. SSH 키 다운로드
# Lightsail 콘솔 → 계정 → SSH 키 → 기본 키 다운로드

# 2. 키 파일 권한 설정 (WSL 필요)
chmod 400 LightsailDefaultKey-ap-northeast-2.pem

# 3. SSH 접속
ssh -i "LightsailDefaultKey-ap-northeast-2.pem" ubuntu@[고정IP]
```

성공하면 아래와 같은 화면이 보입니다:
```
Welcome to Ubuntu 22.04.3 LTS
ubuntu@ip-172-26-12-34:~$
```

---

## Step 4: Docker 설치

SSH로 서버에 접속 후 아래 명령어 실행:

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Docker Compose 설치 (V2)
sudo apt install docker-compose-plugin -y

# 4. 사용자 Docker 권한 부여
sudo usermod -aG docker ubuntu

# 5. 로그아웃 후 재접속 (권한 적용)
exit
# 다시 SSH 접속

# 6. 설치 확인
docker --version
docker compose version
```

---

## Step 5: 프로젝트 업로드

### 방법 A: Git Clone (권장)

```bash
# 1. 프로젝트 폴더 생성
cd ~
mkdir apps && cd apps

# 2. GitHub에서 클론 (저장소 URL 필요)
git clone https://github.com/username/NeighborBid_Auction.git
cd NeighborBid_Auction
```

### 방법 B: 직접 업로드 (SFTP)

FileZilla 등 SFTP 클라이언트 사용:
- 호스트: `고정IP`
- 사용자: `ubuntu`
- 키 파일: 다운로드한 `.pem` 파일

---

## Step 6: 프로덕션 설정 (매우 간편해짐!)

우린 이미 **프로덕션용 설정 파일들(`docker-compose.prod.yml`, `nginx.conf`, `Dockerfile.prod`)을 프로젝트에 포함**시켜 두었습니다.
따라서 서버에서 복잡하게 파일을 수정할 필요 없이, **환경 변수(.env)**만 만들어주면 됩니다.

### 6.1 .env 파일 생성

```bash
nano .env
```

> [!TIP]
> **'nano' 명령어가 안 된다면? (command not found)**
> 혹시 프롬프트가 `C:\Users\...` 로 되어있나요? 그렇다면 현재 **내 컴퓨터(Windows)**에 있는 것입니다.
> `nano`는 리눅스용 편집기이므로, 먼저 **Step 3**를 따라 **SSH로 서버에 접속**한 뒤 실행해주세요.
> (만약 로컬 Windows에서 파일을 만들고 싶다면 `notepad .env`를 입력하세요.)

아래 내용을 복사해서 붙여넣으세요. (값은 본인 것으로 꼭 변경!)

```env
# Django 설정
DJANGO_SECRET_KEY=yoursecretkey
DJANGO_DEBUG=False
ALLOWED_HOSTS=neighborbid.com,www.neighborbid.com,[고정IP]

# 데이터베이스 설정
DB_NAME=neighborbid
DB_USER=postgres
DB_PASSWORD=yoursecurepassword
DB_HOST=postgres
DB_PORT=5432

# Redis 설정
REDIS_HOST=redis
```

**[저장 및 종료 방법]**
- `Ctrl + O` (저장) → `Enter`
- `Ctrl + X` (종료)

> [!IMPORTANT]
> `DJANGO_SECRET_KEY`는 아래 명령어로 생성해서 넣으세요:
> ```bash
> python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

## Step 7: 실행 및 마이그레이션

이제 준비된 **프로덕션용 밀키트**(`docker-compose.prod.yml`)를 사용해서 실행만 하면 됩니다!

```bash
# 1. 이미지 빌드 및 실행 (프로덕션 파일 지정: -f 옵션 사용)
docker compose -f docker-compose.prod.yml up -d --build

# 2. 데이터베이스 마이그레이션
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 3. 관리자 계정 생성
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 4. 정적 파일 모으기 (이미지 빌드 시 자동 실행되지만 확인차)
# (Dockerfile.prod에 포함되어 있어 생략 가능하지만, 에러 시 실행)
# docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. 상태 확인
docker compose -f docker-compose.prod.yml ps
```

> [!TIP]
> 명령어에 매번 `-f docker-compose.prod.yml`을 붙이는 게 귀찮다면?
> `alias dcprod='docker compose -f docker-compose.prod.yml'` 처럼 단축어를 등록해서 쓸 수도 있습니다.


---

## Step 8 (Option): 도메인 없이 IP로 먼저 접속하기 (테스트용)

도메인을 아직 구매하지 않았거나, 먼저 서버가 잘 작동하는지 확인하고 싶다면 이 방법을 사용하세요.

### 1. 설정 변경 (.env)
`.env` 파일의 `ALLOWED_HOSTS`에 고정 IP가 포함되어 있는지 확인합니다.

```env
ALLOWED_HOSTS=neighborbid.com,www.neighborbid.com,[내_고정_IP]
```
*(이미 Step 6에서 설정했다면 추가 조치는 필요 없습니다)*

### 2. 접속 방법
브라우저 주소창에 `http://[고정IP]` 를 입력하여 접속합니다.

> [!WARNING]
> **주의사항**
> 1. **"주의 요망" 표시**: HTTPS(보안 연결)가 아니므로 브라우저 주소창에 경고가 뜹니다.
> 2. **기능 제한**: 위치 정보(Geolocation) 등 HTTPS가 필수인 기능은 작동하지 않습니다.
> 3. **임시 용도**: 실제 서비스 런칭 시에는 반드시 도메인을 연결하고 HTTPS를 적용해야 합니다.

---

## Step 8: 도메인 연결 (정식 런칭)

### 8.1 도메인 구매

추천 도메인 업체:
- **가비아** (korea): gabia.com
- **호스팅KR**: hosting.kr
- **Namecheap** (global): namecheap.com

### 8.2 DNS 설정

도메인 관리 페이지에서:

| 타입 | 호스트 | 값 |
|-----|-------|---|
| A | @ | [Lightsail 고정 IP] |
| A | www | [Lightsail 고정 IP] |

---

## Step 9: SSL 인증서 발급 (Let's Encrypt)

```bash
# 1. certbot 디렉토리 생성
mkdir -p certbot/conf certbot/www

## Step 8: 도메인 구매 및 연결 (상세 가이드)

드디어 나만의 주소(`neighborbid.com`)를 갖는 시간입니다!
한국에서 가장 저렴하고 관리가 편한 **"호스팅케이알(HostingKR)"**을 기준으로 설명드릴게요. (가비아도 비슷합니다.)

### 8.1 도메인 구매하기 (호스팅케이알 기준)

1.  [호스팅케이알](https://www.hosting.kr/) 접속 및 회원가입
2.  검색창에 원하는 도메인 입력 (예: `neighborbid`)
3.  `.com` 또는 `.co.kr` 등 원하는 확장자 선택 후 **[등록신청]**
4.  결제 진행 (1년에 약 1.5만원 ~ 2만원)
5.  **구매 완료!**

### 8.2 DNS 설정 (내 도메인을 AWS 서버로 연결)

구매한 도메인이 우리 AWS 서버(`43.202.xxx.xxx`)를 가리키게 해야 합니다.

1.  호스팅케이알 로그인 → **[나의 서비스]** → **[도메인 관리]**
2.  구매한 도메인 클릭
3.  **[네임서버/DNS]** 탭 클릭 → **[DNS 레코드 관리]** 섹션으로 이동
4.  **[+ 새 레코드 추가]** 버튼 클릭 후 아래 **두 개**를 추가합니다.

**첫 번째 레코드 (메인 주소)**
| 유형 | 호스트(이름) | 값(IP주소) | TTL |
|:---:|:---:|:---:|:---:|
| **A** | **@** (또는 비워둠) | **[AWS 고정 IP]** | 600 |
*(예: 값에 `43.202.137.187` 입력)*

**두 번째 레코드 (www 주소)**
| 유형 | 호스트(이름) | 값(IP주소) | TTL |
|:---:|:---:|:---:|:---:|
| **A** | **www** | **[AWS 고정 IP]** | 600 |

5.  **[저장]** 클릭
6.  **확인**: 브라우저 주소창에 `http://내도메인.com` 입력 시, Django 에러 페이지나 "Welcome to Nginx" 등이 뜨면 성공! (적용까지 10분~1시간 소요될 수 있음)

---

## Step 9: HTTPS (보안 자물쇠) 달기 - 정말 중요!

요즘 웹사이트에 자물쇠(SSL)가 없으면 브라우저가 "주의 요망"이라고 빨간 경고를 띄웁니다.
하지만 걱정 마세요. 우리가 미리 만들어둔 설정 덕분에 **명령어 한 방**이면 끝납니다.

### 9.1 SSL 인증서 발급 (Certbot)

서버 터미널(Git Bash)에서 아래 명령어를 **한 줄씩** 입력하세요.
(명령어 중간에 `neighborbid.com` 부분은 **반드시 본인 도메인으로 바꿔야 합니다!**)

```bash
# 1. Certbot 폴더 만들기 (이미 위에서 자동 생성됐겠지만 확인차)
mkdir -p certbot/conf certbot/www

# 2. 인증서 발급 요청 (★중요: 아래 도메인 부분을 내 껄로 수정해서 복사하세요!)
docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email 내이메일@gmail.com \
    -d 내도메인.com \
    -d www.내도메인.com \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal" nginx
```
*(위 명령어가 너무 길어서 잘 안 되면, 메모장에 복사해서 수정 후 붙여넣으세요)*

### 9.2 성공 확인 및 적용
터미널에 `Successfully received certificate` 라는 문구가 뜨면 성공입니다!
이제 Nginx가 이 인증서를 쓰도록 재시작해 줍니다.

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### 9.3 최종 접속 테스트
크롬 브라우저를 켜고 `https://내도메인.com` 으로 접속해보세요. 주소창 옆에 **자물쇠 아이콘 🔒**이 보이면 런칭 성공입니다!


---

## 🎉 런칭 완료!

축하합니다! 이제 `https://neighborbid.com`으로 접속할 수 있습니다.

### 런칭 후 체크리스트

- [ ] HTTPS 접속 확인
- [ ] 회원가입/로그인 테스트
- [ ] 경매 생성 테스트
- [ ] 실시간 입찰 (WebSocket) 테스트
- [ ] 관리자 페이지 접속 (`/admin/`)

### 유지보수 명령어

```bash
# 로그 확인
docker compose logs -f web

# 서비스 재시작
docker compose restart

# 업데이트 배포
git pull
docker compose build
docker compose up -d
```

---

**작성일**: 2026-01-18
**대상 프로젝트**: NeighborBid (Django 5.2 + Channels + Redis)
