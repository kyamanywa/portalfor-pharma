"""
Django settings for kampala_pharma project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment Configuration Support
try:
    import environ
    env = environ.Env(
        DEBUG=(bool, False),
        SECRET_KEY=(str, 'django-insecure-kampala-pharma-development-key-change-in-production'),
        ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
        USE_2FA=(bool, False),
    )
    # Read .env file if it exists
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        environ.Env.read_env(env_file)
        SECRET_KEY = env('SECRET_KEY')
        DEBUG = env('DEBUG')
        ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
    else:
        # Development fallback
        SECRET_KEY = 'django-insecure-kampala-pharma-development-key-change-in-production'
        DEBUG = True
        ALLOWED_HOSTS = ['*']
        print("⚠️  WARNING: No .env file found. Using development defaults.")
        print("⚠️  Create a .env file for production deployment!")
except ImportError:
    print("⚠️  django-environ not installed. Install with: pip install django-environ")
    SECRET_KEY = 'django-insecure-kampala-pharma-development-key-change-in-production'
    DEBUG = True
    ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # 'daphne',  # Commented out - not installed
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'corsheaders',
    'django_filters',
    # Security and Compliance Apps
    'simple_history',  # Immutable audit trails
    'axes',  # Brute force protection
    'drf_spectacular',  # API documentation
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
        print(f"[OK] {app} - Available")
    except ImportError:
        print(f"[OPTIONAL] {app} - Not installed (optional)")

# Add OTP middleware only if django_otp is available
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',  # Brute force protection (must be after AuthenticationMiddleware)
]

if 'django_otp' in INSTALLED_APPS:
    MIDDLEWARE.append('django_otp.middleware.OTPMiddleware')  # 2FA support
    
MIDDLEWARE.extend([
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.session_timeout.SessionTimeoutMiddleware',  # RE-ENABLED for security
    'simple_history.middleware.HistoryRequestMiddleware',  # Audit trail middleware
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
                'dashboards.context_processors.user_notifications',  # Add notifications context
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
    print("[OPTIONAL] django-environ not installed - using default settings")
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

# Channels Configuration (WebSocket support)
# Using local memory channel layer for development (no Redis required)
if 'channels' in INSTALLED_APPS:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
            # For production with Redis, use:
            # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
            # 'CONFIG': {
            #     "hosts": [("127.0.0.1", 6379)],
            # },
        }
    }
    ASGI_APPLICATION = 'kampala_pharma.routing.application'
    print("[OK] Django Channels: ENABLED (InMemoryChannelLayer)")
else:
    print("[INFO] Django Channels: NOT INSTALLED")

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

# =============================================================================
# SECURITY ENHANCEMENTS
# =============================================================================

# Django Axes - Brute Force Protection (Configurable via .env)
AXES_ENABLED = env.bool('AXES_ENABLED', default=True)
AXES_FAILURE_LIMIT = env.int('AXES_FAILURE_LIMIT', default=5)  # Lock after X failed attempts
AXES_COOLOFF_TIME = env.int('AXES_COOLOFF_TIME', default=1)  # Lockout duration in hours
AXES_LOCKOUT_TEMPLATE = 'accounts/account_locked.html'
AXES_LOCKOUT_URL = '/accounts/locked/'
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]  # Lock by combination of username and IP (more secure)
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_USERNAME_FORM_FIELD = 'username'
AXES_PASSWORD_FORM_FIELD = 'password'
# Use cache for better performance
AXES_CACHE = 'default'

# Authentication Backend (Axes must be first)
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Axes authentication
    'django.contrib.auth.backends.ModelBackend',  # Default Django auth
]

# Password Validation - Enhanced for pharma compliance
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increased from default 8 for pharma compliance
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Simple History - Audit Trail Configuration
SIMPLE_HISTORY_HISTORY_ID_USE_UUID = True  # More secure IDs
SIMPLE_HISTORY_REVERT_DISABLED = True  # Prevent reverting changes (immutability)
SIMPLE_HISTORY_HISTORY_CHANGE_REASON_USE_TEXT_FIELD = True  # Allow detailed reasons

# API Documentation - drf-spectacular
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

SPECTACULAR_SETTINGS = {
    'TITLE': 'KPI Operations Management System API',
    'DESCRIPTION': 'RESTful API for pharmaceutical manufacturing operations',
    'VERSION': SYSTEM_VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'KPI IT Department',
        'email': 'it@kpi.com',
    },
    'LICENSE': {
        'name': 'Proprietary',
    },
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'BMR', 'description': 'Batch Manufacturing Records'},
        {'name': 'Workflow', 'description': 'Production workflow management'},
        {'name': 'Products', 'description': 'Product master data'},
        {'name': 'Quality', 'description': 'Quality control and quarantine'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
}

# Rate Limiting for API Security
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'kampala_pharma.views.ratelimit_error'
SYSTEM_BUILD = 'enterprise-ready'

print("[OK] KPI Operations System - Enhanced Configuration Loaded")
if USE_TWO_FACTOR_AUTH:
    print("[OK] Two-Factor Authentication: ENABLED")
if 'channels' in INSTALLED_APPS:
    print("[OK] Real-time Features: READY")
print("[OK] API Framework: ENABLED")
print("[OK] Security: ENHANCED")

# =============================================================================
# DYNAMIC SETTINGS FROM DATABASE
# =============================================================================
# Load security settings from database if available (overrides .env)
try:
    from accounts.security_settings import SecuritySettings
    
    # Try to load settings from database
    db_settings = SecuritySettings.get_settings()
    
    # Override AXES settings from database
    AXES_ENABLED = db_settings.axes_enabled
    AXES_FAILURE_LIMIT = db_settings.axes_failure_limit
    AXES_COOLOFF_TIME = float(db_settings.axes_cooloff_hours)
    
    # Override password settings
    for validator in AUTH_PASSWORD_VALIDATORS:
        if 'MinimumLengthValidator' in validator.get('NAME', ''):
            validator['OPTIONS'] = {'min_length': db_settings.password_min_length}
    
    print(f"[OK] Security Settings loaded from database (Updated: {db_settings.last_updated.strftime('%Y-%m-%d %H:%M')})")
    
except Exception as e:
    # Database not available yet (migrations) or settings don't exist
    # Use .env defaults
    pass
