"""
Cloud SQL을 사용하는 프로덕션 설정
"""
from .settings import *
import os

# 프로덕션 환경 설정
DEBUG = False
ALLOWED_HOSTS = ['*']

# URL 자동 슬래시 추가
APPEND_SLASH = True

# Cloud SQL (PostgreSQL) 데이터베이스 설정 - Unix Socket 연결
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'bidhub123'),
        'HOST': '/cloudsql/agile-entry-457201-m9:asia-northeast3:bidhub-db',  # Unix socket
        # Cloud SQL Proxy 사용 시 PORT 불필요
        'OPTIONS': {
            'connect_timeout': 60,
        },
    }
}

# 정적 파일 설정
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 미디어 파일 설정 (Google Cloud Storage 사용 권장)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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

# 인증 설정
AUTH_USER_MODEL = 'accounts.User'

# Site ID for allauth
SITE_ID = 1

# Allauth 설정
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# allauth socialaccount settings
SOCIALACCOUNT_PROVIDERS = {
    'kakao': {
        'APP': {
            'client_id': '717318581cabe2d3d608ec057f0f82d5',
            'secret': '',
            'key': ''
        }
    }
}

# Tell allauth to use our custom signup form
ACCOUNT_FORMS = {
    'signup': 'main.forms.CustomSignupForm',
}

# ASGI 설정 (WebSocket 지원)
ASGI_APPLICATION = 'backend.asgi.application'

# Channels Layer 설정 (Cloud Run에서는 InMemory 사용)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

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
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
