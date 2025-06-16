#!/bin/bash
# Cloud Run 시작 스크립트 - Cloud SQL 마이그레이션 포함

set -e

echo "🚀 Starting BidHub application..."

# Cloud SQL 연결 대기
echo "⏳ Waiting for Cloud SQL connection..."
sleep 5

# 데이터베이스 마이그레이션 실행
echo "🔄 Running database migrations..."
python manage.py migrate --noinput --settings=backend.settings_cloudsql

# 정적 파일 수집
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear --settings=backend.settings_cloudsql

echo "✅ Setup complete! Starting ASGI server with WebSocket support..."

# PORT 환경변수 확인 (Cloud Run에서 자동 설정)
if [ -z "$PORT" ]; then
    export PORT=8080
    echo "⚠️  PORT not set, defaulting to 8080"
else
    echo "🔌 Using PORT: $PORT"
fi

# Daphne ASGI 서버 시작 (WebSocket 지원)
# Cloud Run이 자동으로 설정하는 PORT 환경변수를 그대로 사용
exec daphne -b 0.0.0.0 -p $PORT backend.asgi:application
