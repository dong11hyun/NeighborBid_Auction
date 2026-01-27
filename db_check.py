import os
import django
from django.db import connection
from django.db.utils import OperationalError

# 장고 설정 로드
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def check_db_connection():
    print("🔌 데이터베이스 연결 확인 중...")
    try:
        connection.ensure_connection()
        print("✅ 데이터베이스 연결 성공!")
        
        # 테이블 존재 여부 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
            count = cursor.fetchone()[0]
            print(f"📊 현재 생성된 테이블 수: {count}")
            
            if count > 0:
                print("✅ 테이블이 존재합니다. 마이그레이션이 적용된 것으로 보입니다.")
            else:
                print("⚠️ 테이블이 없습니다. 마이그레이션이 필요합니다.")
                
    except OperationalError as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("   -> Docker 컨테이너(db)가 실행 중인지 확인하세요.")
        print("   -> .env 파일의 DB 설정(HOST, PASSWORD 등)이 올바른지 확인하세요.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    check_db_connection()
