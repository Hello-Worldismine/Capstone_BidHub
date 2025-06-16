from .settings import *
import os

# 프로덕션 환경 설정
DEBUG = False
ALLOWED_HOSTS = ['*']

# Cloud SQL PostgreSQL 데이터베이스 설정
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'bidhub123'),
        'HOST': '/cloudsql/agile-entry-457201-m9:asia-northeast3:bidhub-db',
        # Cloud Run에서는 PORT를 지정하지 않음 (Unix socket 사용)
    }
}

# 정적 파일 설정
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 미디어 파일 설정 (업로드된 이미지들)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Channels 및 WebSocket 설정
ASGI_APPLICATION = 'backend.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# WhiteNoise 미들웨어 추가
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# WhiteNoise 설정
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# 보안 설정
SECURE_SSL_REDIRECT = False  # Cloud Run에서는 불필요
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',
]

# 환경 변수에서 설정 로드
SECRET_KEY = os.getenv('SECRET_KEY', SECRET_KEY)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ALCHEMY_RPC = os.getenv('ALCHEMY_RPC')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
OPER_ADDRESS = os.getenv('OPER_ADDRESS')
AES_KEY = os.getenv('AES_KEY')
NAVER_MAPS_CLIENT_ID = os.getenv('NAVER_MAPS_CLIENT_ID')

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}