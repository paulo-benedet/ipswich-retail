import os
import dj_database_url
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DEBUG is disabled.")
    SECRET_KEY = "local-development-only-do-not-use-in-production"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
INSTALLED_APPS = [
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles", "accounts",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware", "config.observability.RequestLoggingMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True, "OPTIONS": {"context_processors": [
        "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3")}}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "welcome"
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG

# The demo credentials are intentionally public; never reuse them for a real account.
DEMO_ENABLED = os.environ.get("DJANGO_DEMO_ENABLED", "1") == "1"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "Retail-Demo-73!"
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=0)
if os.environ.get("RENDER") == "true":
    if not DATABASE_URL:
        raise ImproperlyConfigured("Hosted deployment requires DATABASE_URL.")
    # Render terminates HTTPS and supplies this header at its trusted proxy.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])
        CSRF_TRUSTED_ORIGINS = ["https://" + os.environ["RENDER_EXTERNAL_HOSTNAME"]]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MONITORING_TOKEN = os.environ.get("MONITORING_TOKEN", "")
APP_REVISION = os.environ.get("RENDER_GIT_COMMIT", os.environ.get("APP_REVISION", "local"))
LOGGING = {
    "version": 1, "disable_existing_loggers": False,
    "formatters": {"safe": {"()": "config.observability.SafeJsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "safe"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "retail": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
