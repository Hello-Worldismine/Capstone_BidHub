#!/bin/bash

# 프로젝트 설정
PROJECT_ID="agile-entry-457201-m9"
SERVICE_NAME="bidhub-app"
REGION="asia-northeast3"  # 서울 리전
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 BidHub 앱을 Google Cloud Run에 배포합니다..."

# Google Cloud 설정
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
echo "📡 필요한 API를 활성화합니다..."
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com

# Docker 이미지 빌드
echo "� Docker 이미지를 빌드합니다..."
docker build -t $IMAGE_NAME .

# Docker 이미지 푸시
echo "📤 Docker 이미지를 Google Container Registry에 푸시합니다..."
docker push $IMAGE_NAME

# Cloud Run 배포
echo "☁️ Cloud Run에 배포합니다..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars="DJANGO_SETTINGS_MODULE=backend.settings_prod" \
    --set-env-vars="SECRET_KEY=${SECRET_KEY:-your-secret-key-here}"

echo "✅ 배포 완료!"
echo "🌐 서비스 URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"