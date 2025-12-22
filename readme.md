#### 실시간 경매 프로젝트
##### 설치 메뉴얼
```bash
1. 가상환경 설치
python -m venv venv
2. 윈도우 가상환경 활성화
venv\Scripts\activate
3. 필요 라이브러리 설치
pip install -r requirements.txt
```
##### 설계도(migrations 파일) 바탕 DB 생성
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
##### 도커
- 서버켜기
```docker-compose up```

- 서버 켜기 (새로 빌드),(패키지 설치하거나 설정 바꿨을 때)
```docker-compose up --build```  

- DB 마이그레이션 생성,
```docker-compose exec web python manage.py makemigrations```

- DB 마이그레이션 적용,
```docker-compose exec web python manage.py migrate```

- 관리자 계정 생성,
```docker-compose exec web python manage.py createsuperuser```

- 셸(Shell) 접속,
```docker-compose exec web python manage.py shell```

