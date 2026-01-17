"""
Django settings for Real Estate LLM project.
Base settings shared across all environments.
"""

import os
from pathlib import Path
from datetime import timedelta
from urllib.parse import quote
import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file (explicitly, not .env.local)
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
else:
    raise FileNotFoundError(f"Missing {env_file} configuration file")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Application definition
INSTALLED_APPS = [
    'daphne',  # Must be first for WebSocket support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'channels',  # WebSocket support
    
    # Local apps
    'apps.tenants',
    'apps.users',
    'apps.properties',
    'apps.documents',
    'apps.conversations',
    'apps.chat',
    'apps.ingestion',
]

MIDDLEWARE = [
    'core.middleware.HostValidationMiddleware',  # Custom host validation first
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.tenants.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Database
# Priority: LOCAL_DB_* vars > DATABASE_URL > default
if env('LOCAL_DB_NAME', default=None):
    # Local development mode with PostgreSQL
    # Escape special characters in password for proper URL encoding
    db_password = env('LOCAL_DB_PASSWORD', default='')
    db_password_encoded = quote(db_password, safe='')
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('LOCAL_DB_NAME'),
            'USER': env('LOCAL_DB_USER'),
            'PASSWORD': db_password,  # psycopg2 will handle encoding
            'HOST': env('LOCAL_DB_HOST', default='localhost'),
            'PORT': env('LOCAL_DB_PORT', default='5432'),
        }
    }
else:
    # Production mode (uses DATABASE_URL)
    DATABASES = {
        'default': env.db('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/real_estate_llm')
    }

# Enable connection pooling
# Enable connection pooling and Postgres options
if 'postgresql' in DATABASES['default']['ENGINE']:
    DATABASES['default']['CONN_MAX_AGE'] = 600
    DATABASES['default']['OPTIONS'] = {
        'options': '-c search_path=public',
    }

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Costa_Rica'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Changed from IsAuthenticated for development
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'core.utils.exception_handler.custom_exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True

# Redis Configuration (optional - fallback to dummy cache if not available)
REDIS_URL = env('REDIS_URL', default=None)

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PARSER_CLASS': 'redis.connection.HiredisParser',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
            },
            'KEY_PREFIX': 'real_estate_llm',
            'TIMEOUT': 3600,  # 1 hour default
        },
        'embeddings': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'DB': 1,
            },
            'KEY_PREFIX': 'embeddings',
            'TIMEOUT': 86400 * 7,  # 7 days
        }
    }
else:
    # Use dummy cache (no caching) when Redis is not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
        'embeddings': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# LLM Configuration
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_MODEL_CHAT = env('OPENAI_MODEL_CHAT', default='gpt-4o-mini')
OPENAI_MODEL_COMPLEX = env('OPENAI_MODEL_COMPLEX', default='gpt-4o')
OPENAI_EMBEDDING_MODEL = env('OPENAI_EMBEDDING_MODEL', default='text-embedding-3-small')
OPENAI_MAX_TOKENS = env.int('OPENAI_MAX_TOKENS', default=4000)
OPENAI_TEMPERATURE = env.float('OPENAI_TEMPERATURE', default=0.3)

ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
ANTHROPIC_MODEL = env('ANTHROPIC_MODEL', default='claude-3-5-sonnet-20240620')
ANTHROPIC_MAX_TOKENS = env.int('ANTHROPIC_MAX_TOKENS', default=4000)

# RAG Configuration
LLM_CACHE_ENABLED = env.bool('LLM_CACHE_ENABLED', default=True)
LLM_CACHE_TTL_HOURS = env.int('LLM_CACHE_TTL_HOURS', default=24)
SEMANTIC_CACHE_THRESHOLD = env.float('SEMANTIC_CACHE_THRESHOLD', default=0.95)
VECTOR_SEARCH_TOP_K = env.int('VECTOR_SEARCH_TOP_K', default=5)
HYBRID_SEARCH_ALPHA = env.float('HYBRID_SEARCH_ALPHA', default=0.5)
EMBEDDING_DIMENSIONS = env.int('EMBEDDING_DIMENSIONS', default=1536)

# Scraping Configuration
SCRAPING_TIMEOUT_SECONDS = env.int('SCRAPING_TIMEOUT_SECONDS', default=30)
SCRAPING_USER_AGENT = env('SCRAPING_USER_AGENT', 
    default='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
SCRAPING_RATE_LIMIT_PER_SECOND = env.int('SCRAPING_RATE_LIMIT_PER_SECOND', default=1)
PLAYWRIGHT_HEADLESS = env.bool('PLAYWRIGHT_HEADLESS', default=True)

# Residential Proxy for Cloudflare-protected sites (optional)
# Format: http://username:password@proxy-server.com:port
# Example providers: BrightData, Smartproxy, Oxylabs, ProxyEmpire
RESIDENTIAL_PROXY_URL = env('RESIDENTIAL_PROXY_URL', default=None)

# Scrapfly API for advanced anti-bot bypass (replaces residential proxies)
# Get your API key from: https://scrapfly.io/dashboard
SCRAPFLY_API_KEY = env('SCRAPFLY_API_KEY', default=None)
SCRAPFLY_ENABLED = env.bool('SCRAPFLY_ENABLED', default=True)

# Multi-Tenancy
TENANT_ISOLATION_ENABLED = env.bool('TENANT_ISOLATION_ENABLED', default=True)
DEFAULT_TENANT_ID = env('DEFAULT_TENANT_ID', default=None)

# Feature Flags
ENABLE_PROPERTY_SCRAPING = env.bool('ENABLE_PROPERTY_SCRAPING', default=True)
ENABLE_PDF_PROCESSING = env.bool('ENABLE_PDF_PROCESSING', default=True)
ENABLE_SEMANTIC_CACHE = env.bool('ENABLE_SEMANTIC_CACHE', default=True)
ENABLE_ASYNC_EMBEDDINGS = env.bool('ENABLE_ASYNC_EMBEDDINGS', default=True)

# Chat Configuration
MAX_CONVERSATION_HISTORY = env.int('MAX_CONVERSATION_HISTORY', default=10)
MAX_CONTEXT_TOKENS = env.int('MAX_CONTEXT_TOKENS', default=25000)
STREAMING_ENABLED = env.bool('STREAMING_ENABLED', default=True)

# Currency and Unit Conversion
USD_TO_CRC_RATE = env.float('USD_TO_CRC_RATE', default=520.0)
SQFT_TO_SQM_FACTOR = env.float('SQFT_TO_SQM_FACTOR', default=0.092903)

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': env('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
