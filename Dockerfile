# 1. 파이썬 3.11 버전을 기반으로 합니다.
FROM python:3.11-slim

# 2. 파이썬 출력을 버퍼링 없이 바로 보여주게 설정 (로그 확인용)
ENV PYTHONUNBUFFERED=1

# 3. 작업 폴더 설정
WORKDIR /app

# 4. 패키지 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . /app/

# 6. 포트 열기 (장고 기본 포트)
EXPOSE 8000

# 7. 서버 실행 명령어 (ASGI 모드로 실행)
# 개발 중에는 runserver를 쓰지만, Channels가 설치되면 runserver도 자동으로 ASGI를 지원합니다.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]