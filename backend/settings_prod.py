from .settings import *
import os

# 프로덕션 환경 설정
DEBUG = False
ALLOWED_HOSTS = ['*']

# SQLite 데이터베이스 설정 (기존 DB 사용)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # 기존 DB 파일 사용
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

# 정적 파일 설정
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise 미들웨어 추가
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

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