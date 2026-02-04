# 📘 설계문서 3: Nginx 리버스 프록시 및 프로젝트별 Docker 구성

> **대상**: EC2를 처음 사용하는 주니어 개발자
> **목표**: Nginx 설정 및 5개 프로젝트 Docker 구성 완료

---

## 1. Nginx 리버스 프록시 이해하기

### 🎯 동작 원리

```
사용자 브라우저
      ↓
portfolio.example.com/project1/
      ↓
┌─────────────────────────────────────────┐
│              Nginx (80/443)              │
│   "project1 경로네? → 8001로 보내자!"     │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│         Docker Container (8001)          │
│         Django + PostgreSQL              │
└─────────────────────────────────────────┘
```

---

## 2. Nginx 설정 파일 작성

### Step 1: 메인 Nginx 설정 (`~/nginx/nginx.conf`)

```bash
cat > ~/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 50M;

    # Gzip 압축
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    include /etc/nginx/conf.d/*.conf;
}
EOF
```

### Step 2: 프로젝트 라우팅 설정 (`~/nginx/conf.d/default.conf`)

```bash
cat > ~/nginx/conf.d/default.conf << 'EOF'
# ===========================================
# 각 프로젝트로 연결하는 upstream 정의
# ===========================================
upstream project1 {
    server project1-app:8000;  # Django/Gunicorn
}

upstream project2 {
    server project2-app:8000;  # FastAPI/Uvicorn
}

upstream project3 {
    server project3-app:8000;
}

upstream project4 {
    server project4-app:8000;
}

upstream project5 {
    server project5-app:8000;
}

# ===========================================
# 메인 서버 블록
# ===========================================
server {
    listen 80;
    server_name portfolio.example.com _;  # 도메인 또는 IP

    # 메인 포트폴리오 페이지 (정적 파일)
    location / {
        root /usr/share/nginx/html/portfolio;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # ========================
    # 프로젝트 1: NeighborBid (경매)
    # ========================
    location /project1/ {
        rewrite ^/project1/(.*)$ /$1 break;
        proxy_pass http://project1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name /project1;
    }

    location /project1/static/ {
        alias /usr/share/nginx/html/project1/static/;
    }

    # ========================
    # 프로젝트 2: FastAPI
    # ========================
    location /project2/ {
        rewrite ^/project2/(.*)$ /$1 break;
        proxy_pass http://project2;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ========================
    # 프로젝트 3, 4, 5 (동일 패턴)
    # ========================
    location /project3/ {
        rewrite ^/project3/(.*)$ /$1 break;
        proxy_pass http://project3;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /project4/ {
        rewrite ^/project4/(.*)$ /$1 break;
        proxy_pass http://project4;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /project5/ {
        rewrite ^/project5/(.*)$ /$1 break;
        proxy_pass http://project5;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
```

---

## 3. 프로젝트별 Docker Compose 구성

### 📦 프로젝트 1: Django + PostgreSQL 예시

**파일 위치**: `~/projects/project1-neighborbid/docker-compose.yml`

```yaml
version: '3.8'

services:
  # Django 애플리케이션
  app:
    build:
      context: ./app
      dockerfile: Dockerfile.prod
    container_name: project1-app
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    networks:
      - portfolio-network
      - project1-internal
    depends_on:
      - db

  # PostgreSQL 데이터베이스
  db:
    image: postgres:15-alpine
    container_name: project1-db
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - project1-internal

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  portfolio-network:
    external: true  # Nginx와 통신용
  project1-internal:
    driver: bridge  # DB와만 통신
```

### 📦 프로젝트 2: FastAPI + OpenSearch 예시

**파일 위치**: `~/projects/project2-fastapi/docker-compose.yml`

```yaml
version: '3.8'

services:
  # FastAPI 애플리케이션
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: project2-app
    restart: unless-stopped
    env_file:
      - .env
    networks:
      - portfolio-network
      - project2-internal
    depends_on:
      - opensearch

  # OpenSearch
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: project2-opensearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    networks:
      - project2-internal

volumes:
  opensearch_data:

networks:
  portfolio-network:
    external: true
  project2-internal:
    driver: bridge
```

### 📦 프로젝트 3: Django + Kafka 예시

**파일 위치**: `~/projects/project3/docker-compose.yml`

```yaml
version: '3.8'

services:
  app:
    build: ./app
    container_name: project3-app
    restart: unless-stopped
    env_file:
      - .env
    networks:
      - portfolio-network
      - project3-internal
    depends_on:
      - kafka
      - db

  db:
    image: postgres:15-alpine
    container_name: project3-db
    env_file:
      - .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - project3-internal

  # Zookeeper (Kafka 의존)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: project3-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    networks:
      - project3-internal

  # Kafka
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: project3-kafka
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    networks:
      - project3-internal

volumes:
  postgres_data:

networks:
  portfolio-network:
    external: true
  project3-internal:
    driver: bridge
```

---

## 4. Nginx Docker 컨테이너 구성

**파일 위치**: `~/nginx/docker-compose.yml`

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: portfolio-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./conf.d:/etc/nginx/conf.d:ro
      - ./html:/usr/share/nginx/html:ro
      - ./ssl:/etc/nginx/ssl:ro
      # 각 프로젝트 정적 파일 마운트
      - project1_static:/usr/share/nginx/html/project1/static:ro
    networks:
      - portfolio-network

volumes:
  project1_static:
    external: true
    name: project1-neighborbid_static_volume

networks:
  portfolio-network:
    external: true
```

---

## 5. SSL 인증서 설정 (Let's Encrypt)

### Certbot 설치 및 인증서 발급

```bash
# Certbot 설치
sudo apt install -y certbot

# Nginx 중지 후 인증서 발급 (standalone 모드)
docker compose -f ~/nginx/docker-compose.yml down

sudo certbot certonly --standalone \
    -d portfolio.example.com \
    --email your-email@example.com \
    --agree-tos \
    --non-interactive

# 인증서 위치 (자동 생성됨)
# /etc/letsencrypt/live/portfolio.example.com/fullchain.pem
# /etc/letsencrypt/live/portfolio.example.com/privkey.pem

# Nginx SSL 폴더로 복사
sudo cp /etc/letsencrypt/live/portfolio.example.com/fullchain.pem ~/nginx/ssl/
sudo cp /etc/letsencrypt/live/portfolio.example.com/privkey.pem ~/nginx/ssl/
sudo chown -R $USER:$USER ~/nginx/ssl/
```

### HTTPS 설정 추가 (`~/nginx/conf.d/default.conf` 수정)

```nginx
server {
    listen 80;
    server_name portfolio.example.com;
    
    # HTTP → HTTPS 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name portfolio.example.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # 기존 location 블록들...
}
```

---

## 6. 배포 워크플로우

### 🚀 전체 시작 순서

```bash
# 1. Docker 네트워크 확인
docker network ls | grep portfolio-network

# 2. 각 프로젝트 시작 (순서대로)
cd ~/projects/project1-neighborbid && docker compose up -d
cd ~/projects/project2-fastapi && docker compose up -d
cd ~/projects/project3 && docker compose up -d
cd ~/projects/project4 && docker compose up -d
cd ~/projects/project5 && docker compose up -d

# 3. Nginx 시작 (마지막)
cd ~/nginx && docker compose up -d

# 4. 상태 확인
docker ps
```

### 📋 편의용 스크립트

**파일 위치**: `~/start-all.sh`

```bash
#!/bin/bash
echo "🚀 Starting all portfolio projects..."

PROJECTS=("project1-neighborbid" "project2-fastapi" "project3" "project4" "project5")

for project in "${PROJECTS[@]}"; do
    echo "Starting $project..."
    cd ~/projects/$project && docker compose up -d
done

echo "Starting Nginx..."
cd ~/nginx && docker compose up -d

echo "✅ All services started!"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

```bash
# 실행 권한 부여 및 실행
chmod +x ~/start-all.sh
./start-all.sh
```

---

## 7. 모니터링 및 로그 확인

```bash
# 특정 컨테이너 로그
docker logs -f project1-app

# 전체 리소스 사용량
docker stats

# Nginx 에러 로그
docker logs portfolio-nginx

# 프로젝트 상태 확인
curl -I http://localhost/project1/
curl -I http://localhost/project2/
```

---

## 8. 최종 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            AWS EC2 (t3.large)                            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         Nginx Container                            │ │
│  │                    (80/443 → 리버스 프록시)                         │ │
│  └──────────────────────────┬─────────────────────────────────────────┘ │
│                              │                                           │
│              portfolio-network (Docker Network)                          │
│  ┌──────────────────────────┼─────────────────────────────────────────┐ │
│  │                          ↓                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │  Project 1   │  │  Project 2   │  │  Project 3   │  ...         │ │
│  │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │              │ │
│  │  │  │ Django │  │  │  │FastAPI │  │  │  │ Django │  │              │ │
│  │  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │              │ │
│  │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │              │ │
│  │  │  │Postgres│  │  │  │OpenSrch│  │  │  │ Kafka  │  │              │ │
│  │  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │              │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 핵심 요약

| 단계 | 작업 |
|------|------|
| 1 | EC2 생성 + SSH 접속 |
| 2 | Docker & Docker Compose 설치 |
| 3 | Docker 네트워크 생성 (`portfolio-network`) |
| 4 | 각 프로젝트 Docker Compose 작성 |
| 5 | Nginx 리버스 프록시 설정 |
| 6 | SSL 인증서 발급 |
| 7 | 전체 시작 및 테스트 |

---

## 🎓 추가 학습 권장

1. **Docker 기본**: `docker run`, `docker build`, `docker compose` 명령어
2. **Nginx 기본**: `server`, `location`, `proxy_pass` 개념
3. **네트워크**: Docker 네트워크, 포트 바인딩 이해
4. **모니터링**: `htop`, `docker stats`, 로그 관리

> ✅ 이 구조로 배포하면 **실무형 인프라 경험**을 어필할 수 있습니다!
