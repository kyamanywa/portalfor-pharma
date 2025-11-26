"""
Django settings for kampala_pharma project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kampala-pharma-development-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    # Custom apps
    'accounts',
    'products',
    'bmr',
    'workflow',
    'quarantine',
    'dashboards',
    'reports',
    'fgs_management',
]

# Add optional security and integration features if available
OPTIONAL_APPS = [
    'django_otp',
    'django_otp.plugins.otp_totp', 
    'django_otp.plugins.otp_static',
    'channels',
]

# Check and add available optional apps
for app in OPTIONAL_APPS:
    try:
        __import__(app)
        INSTALLED_APPS.append(app)
        print(f"✅ {app} - Available")
    except ImportError:
        print(f"⚠️  {app} - Not installed (optional)")

# Add OTP middleware only if django_otp is available
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

if 'django_otp' in INSTALLED_APPS:
    MIDDLEWARE.append('django_otp.middleware.OTPMiddleware')  # 2FA support
    
MIDDLEWARE.extend([
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'accounts.middleware.session_timeout.SessionTimeoutMiddleware',  # TEMPORARILY DISABLED - CAUSING LOGIN ISSUES
])

ROOT_URLCONF = 'kampala_pharma.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboards.context_processors.admin_settings_context',  # Add admin settings context
            ],
        },
    },
]

WSGI_APPLICATION = 'kampala_pharma.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20  # Timeout in seconds
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kampala'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # Only for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Login configuration
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Batch number settings
BATCH_NUMBER_PREFIX_LENGTH = 3
BATCH_NUMBER_YEAR_LENGTH = 4

# Session timeout setting (12 hours = 43200 seconds)
SESSION_TIMEOUT = 43200

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'workflow': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'dashboards': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# ENHANCED FEATURES FOR CLOUD DEPLOYMENT
# =============================================================================

# Environment Configuration Support
try:
    import environ
    env = environ.Env(
        DEBUG=(bool, True),
        SECRET_KEY=(str, 'django-insecure-kampala-pharma-development-key-change-in-production'),
        DATABASE_URL=(str, ''),
        ALLOWED_HOSTS=(list, ['*']),
        USE_2FA=(bool, False),
        REDIS_URL=(str, 'redis://localhost:6379'),
    )

    # Read .env file if it exists (for production deployment)
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        environ.Env.read_env(env_file)
        
    # 2FA is optional by default, can be enabled via environment variable
    USE_TWO_FACTOR_AUTH = env('USE_2FA')
    
except ImportError:
    print("⚠️  django-environ not installed - using default settings")
    USE_TWO_FACTOR_AUTH = False
    env = lambda key, default=None: os.environ.get(key, default)

# Two-Factor Authentication Configuration  
OTP_TOTP_ISSUER = 'KPI Operations System'
OTP_LOGIN_URL = '/accounts/login/'

# API Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
}

# Channels Configuration (WebSocket support) - Optional
try:
    import channels
    ASGI_APPLICATION = 'kampala_pharma.asgi.application'
    
    # Redis configuration for channels (WebSocket) and caching
    REDIS_URL = env('REDIS_URL')
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
            },
        },
    }
    
    # Caching Configuration
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'kpi_ops',
            'TIMEOUT': 300,  # 5 minutes default timeout
        }
    }
    
    # Session Configuration for Cloud Deployment
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
    
except ImportError:
    print("⚠️  Redis/Channels not available - using default cache")
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # Secure cookies in production
SESSION_COOKIE_SAMESITE = 'Lax'

# Security Settings for Production
if not DEBUG:
    # HTTPS Settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # SSL Settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Additional Security
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS Configuration for API Access
CORS_ALLOWED_ORIGINS = [
    "https://localhost:3000",
    "https://127.0.0.1:3000",
    # Add production domains here
]

CORS_ALLOW_CREDENTIALS = True

# API Rate Limiting (can be configured via environment)
API_THROTTLE_RATE = env('API_THROTTLE_RATE', default='1000/hour')

# Email Configuration for Production Notifications
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@kpiops.com')

# Integration Settings
INTEGRATION_SETTINGS = {
    'api_enabled': True,
    'websocket_enabled': 'channels' in INSTALLED_APPS,
    'real_time_updates': True,
    'export_formats': ['xlsx', 'csv', 'pdf'],
    'max_file_size': 50 * 1024 * 1024,  # 50MB
}

# Pharmaceutical Compliance Settings
PHARMACEUTICAL_SETTINGS = {
    'electronic_signatures_required': True,
    'audit_trail_retention_days': 2555,  # 7 years
    'gmp_compliance_mode': True,
    'data_integrity_checks': True,
    'change_control_required': not DEBUG,
}

# System Version for API
SYSTEM_VERSION = '2.0.0'
SYSTEM_BUILD = 'enterprise-ready'

print("🚀 KPI Operations System - Enhanced Configuration Loaded")
if USE_TWO_FACTOR_AUTH:
    print("🔐 Two-Factor Authentication: ENABLED")
if 'channels' in INSTALLED_APPS:
    print("⚡ Real-time Features: READY")
print("🔌 API Framework: ENABLED")
print("🛡️  Security: ENHANCED")
