from pathlib import Path
import os
from corsheaders.defaults import default_headers



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-l%7#2e3h4pbq@e7ugz)tui=x(0^v#jx0wczdah3we888y5b$+0",
)
DEBUG = True

#DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost",
                 "coderr.selcuk-kocyigit.de",
                  "api.selcuk-kocyigit.de",
                 "34.13.180.11", ]

CSRF_TRUSTED_ORIGINS = [
    "https://api.selcuk-kocyigit.de",
    "https://coderr.selcuk-kocyigit.de"
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "coder_app",
    "rest_framework",
    "corsheaders",
    "rest_framework.authtoken",
    "django_filters",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

#CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = True 
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]        

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://192.168.2.101:5501",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "http://localhost:5500",
    "https://coderr.selcuk-kocyigit.de",
    
]

ROOT_URLCONF = "Coder.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Coder.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
#STATIC_ROOT = BASE_DIR / "staticfiles"

STATIC_ROOT = BASE_DIR / "static" 
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/day",
        "user": "10000/day",
        "question-scope": "100/day",
        "question": "400/day",
        "question-get": "100/day",
        "question-post": "50/day",
        "question-put": "50/day",
        "question-patch": "50/day",
        "question-delete": "50/day",
        "question-options": "50/day",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
