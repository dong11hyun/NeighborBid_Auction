# 📘 설계문서 2: EC2 초기 설정 및 Docker 환경 구축

> **대상**: EC2를 처음 사용하는 주니어 개발자
> **목표**: EC2 인스턴스에 Docker 환경 구축 완료

---

## 1. EC2 인스턴스 생성 (AWS 콘솔)

### Step 1: EC2 대시보드 접속

```
1. AWS 콘솔 로그인 (https://console.aws.amazon.com)
2. 상단 검색창에 "EC2" 입력 후 클릭
3. 좌측 메뉴에서 "인스턴스" → "인스턴스 시작" 클릭
```

### Step 2: 인스턴스 설정

| 항목 | 설정값 | 설명 |
|------|--------|------|
| 이름 | `portfolio-server` | 식별하기 쉬운 이름 |
| OS | Ubuntu Server 22.04 LTS | 안정적, 자료 많음 |
| 인스턴스 유형 | t3.large | 8GB RAM, 5개 프로젝트용 |
| 키 페어 | 새로 생성 또는 기존 사용 | **절대 분실 금지!** |
| 스토리지 | 30GB gp3 | SSD, 빠른 속도 |

### Step 3: 보안 그룹 설정

```
┌─────────────────────────────────────────────────────────┐
│                    보안 그룹 규칙                         │
├──────────────┬──────────┬──────────────────────────────┤
│ 유형         │ 포트     │ 소스                          │
├──────────────┼──────────┼──────────────────────────────┤
│ SSH          │ 22       │ 내 IP (또는 0.0.0.0/0)       │
│ HTTP         │ 80       │ 0.0.0.0/0 (모든 곳에서)      │
│ HTTPS        │ 443      │ 0.0.0.0/0 (모든 곳에서)      │
└──────────────┴──────────┴──────────────────────────────┘
```

> ⚠️ **보안 주의**: SSH는 가능하면 "내 IP"로 제한하세요!

---

## 2. EC2 접속하기 (SSH)

### Windows (PowerShell)

```powershell
# 키 파일이 있는 폴더로 이동
cd C:\Users\YourName\Downloads

# SSH 접속 (your-key.pem은 다운받은 키 파일명)
ssh -i "your-key.pem" ubuntu@<EC2-Public-IP>

# 예시
ssh -i "portfolio-key.pem" ubuntu@13.125.xxx.xxx
```

### 첫 접속 시 나오는 메시지

```
Are you sure you want to continue connecting (yes/no)?
```
→ `yes` 입력 후 Enter

---

## 3. 서버 초기 설정

### Step 1: 시스템 업데이트

```bash
# 패키지 목록 업데이트
sudo apt update

# 설치된 패키지 업그레이드
sudo apt upgrade -y
```

### Step 2: 필수 패키지 설치

```bash
# 필수 도구들 설치
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools
```

### Step 3: 스왑 메모리 설정 (권장)

> 💡 메모리 부족 시 비상용 디스크 메모리

```bash
# 4GB 스왑 파일 생성
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 재부팅 후에도 유지되도록 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```

---

## 4. Docker 설치

### Step 1: 이전 버전 제거 (혹시 있다면)

```bash
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null
```

### Step 2: Docker 저장소 설정

```bash
# 필요한 패키지 설치
sudo apt install -y ca-certificates curl gnupg lsb-release

# Docker 공식 GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 저장소 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Step 3: Docker 설치

```bash
# 패키지 목록 업데이트
sudo apt update

# Docker 설치
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 docker 사용)
sudo usermod -aG docker $USER

# 변경사항 적용을 위해 재로그인 필요
exit
```

재접속 후:
```bash
ssh -i "your-key.pem" ubuntu@<EC2-Public-IP>
```

### Step 4: 설치 확인

```bash
# Docker 버전 확인
docker --version
# 출력 예: Docker version 24.0.7, build afdd53b

# Docker Compose 버전 확인
docker compose version
# 출력 예: Docker Compose version v2.21.0

# Docker 테스트
docker run hello-world
```

---

## 5. 프로젝트 디렉토리 구조 생성

### 폴더 구조

```
/home/ubuntu/
├── portfolio/                    # 메인 포트폴리오 (선택사항)
│   └── docker-compose.yml
│
├── projects/                     # 모든 프로젝트 폴더
│   ├── project1-neighborbid/     # 프로젝트 1
│   │   ├── docker-compose.yml
│   │   ├── .env
│   │   └── app/
│   │
│   ├── project2-fastapi/         # 프로젝트 2
│   │   ├── docker-compose.yml
│   │   ├── .env
│   │   └── app/
│   │
│   ├── project3/                 # 프로젝트 3
│   ├── project4/                 # 프로젝트 4
│   └── project5/                 # 프로젝트 5
│
└── nginx/                        # Nginx 설정
    ├── nginx.conf
    └── conf.d/
        └── default.conf
```

### 폴더 생성 명령어

```bash
# 프로젝트 폴더 생성
mkdir -p ~/projects/{project1-neighborbid,project2-fastapi,project3,project4,project5}

# Nginx 설정 폴더 생성
mkdir -p ~/nginx/conf.d

# 구조 확인
tree ~/projects ~/nginx
```

---

## 6. Docker 네트워크 설정

### 왜 필요한가?

> Docker 네트워크를 사용하면 컨테이너들이 서로 통신 가능!

```
┌─────────────────────────────────────────────────────────┐
│             portfolio-network (Docker Network)           │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Nginx    │←→│ Project1 │←→│ Project2 │  ...         │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 네트워크 생성

```bash
# 포트폴리오용 공통 네트워크 생성
docker network create portfolio-network

# 확인
docker network ls
```

---

## 7. 환경 변수 템플릿 생성

### `.env.template` 파일 (각 프로젝트 공통)

```bash
cat > ~/projects/.env.template << 'EOF'
# ======================
# 애플리케이션 설정
# ======================
DEBUG=False
SECRET_KEY=your-secret-key-here

# ======================
# 데이터베이스 설정
# ======================
POSTGRES_DB=dbname
POSTGRES_USER=dbuser
POSTGRES_PASSWORD=dbpassword
DATABASE_URL=postgresql://dbuser:dbpassword@db:5432/dbname

# ======================
# 포트 설정 (프로젝트마다 다르게!)
# ======================
APP_PORT=8001

# ======================
# 기타
# ======================
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
EOF
```

---

## 8. Git 설정 (프로젝트 가져오기용)

```bash
# Git 사용자 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# SSH 키 생성 (GitHub/GitLab 접속용)
ssh-keygen -t ed25519 -C "your.email@example.com"

# 생성된 공개키 확인 (이걸 GitHub에 등록)
cat ~/.ssh/id_ed25519.pub
```

---

## 9. 상태 확인 체크리스트

```bash
# 각 항목 확인
echo "=== 시스템 정보 ==="
uname -a

echo "=== 메모리 상태 ==="
free -h

echo "=== 디스크 사용량 ==="
df -h

echo "=== Docker 상태 ==="
docker --version
docker compose version

echo "=== Docker 네트워크 ==="
docker network ls

echo "=== 폴더 구조 ==="
ls -la ~/projects
```

---

## 🎯 이 문서 완료 후 상태

- [x] EC2 인스턴스 생성 완료
- [x] SSH 접속 가능
- [x] Docker & Docker Compose 설치 완료
- [x] 프로젝트 디렉토리 구조 생성 완료
- [x] Docker 네트워크 설정 완료
- [x] Git 설정 완료

---

## 📌 다음 문서

**[📘 설계문서 3](./3_Nginx_리버스프록시_및_프로젝트별_Docker_구성.md)** 에서:
- Nginx 리버스 프록시 설정
- 각 프로젝트별 Docker Compose 구성
- HTTPS (SSL) 인증서 설정
- 실제 프로젝트 배포 방법
