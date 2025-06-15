import os
from .settings import *

# 환경변수 로드
DEBUG = os.getenv('DEBUG', '0').lower() in ['true', '1', 'on']
SECRET_KEY = os.getenv('SECRET_KEY', SECRET_KEY)

# 허용 호스트
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# 데이터베이스 설정
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
            'init_command': '''
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA cache_size=1000;
                PRAGMA temp_store=memory;
                PRAGMA foreign_keys=ON;
            ''',
        },
    }
}

# 정적 파일
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 미디어 파일
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# WhiteNoise 미들웨어
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# 보안 설정
if os.getenv('SECURE_SSL_REDIRECT', '0') == '1':
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# CORS 설정
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://*.run.app",
    "https://*.googleusercontent.com",
]

# CSRF 설정
CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',
]

# 블록체인 설정
ALCHEMY_RPC = os.getenv('ALCHEMY_RPC')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
OPER_ADDRESS = os.getenv('OPER_ADDRESS')

# AI 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 암호화 설정
AES_KEY = os.getenv('AES_KEY')

# 지도 API 설정
NAVER_MAPS_CLIENT_ID = os.getenv('NAVER_MAPS_CLIENT_ID')

# Redis 설정 (Cloud Run에서는 사용하지 않을 수 있음)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

# 로깅 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'backend': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# 캐시 설정 (Redis 없이 로컬 메모리 캐시 사용)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# 세션 설정
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24시간

# 파일 업로드 설정
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB