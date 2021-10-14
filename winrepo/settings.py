import os
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ENV = config('ENV', default='Local')

ALLOWED_HOSTS = \
    ['*'] \
    if DEBUG else \
    ['localhost', '127.0.0.1', 'winrepo.org', 'winrepo.pythonanywhere.com']


INSTALLED_APPS = [
    'profiles',
    'multiselectfield',
    'crispy_forms',
    'captcha',
    'bootstrap4',
    'dal',
    'dal_select2',
    'robots',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'winrepo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(BASE_DIR, 'templates')), ],
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

WSGI_APPLICATION = 'winrepo.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'TEST': {
            'NAME': config('DB_TEST_NAME'),
        }
    }
}

LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = 'profiles:user'
LOGOUT_REDIRECT_URL = 'profiles:home'

AUTH_USER_MODEL = 'profiles.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = ['profiles.backends.EmailOrUsernameModelBackend']

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "static-collected")

# reCaptcha settings
RECAPTCHA_PUBLIC_KEY = config('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = config('RECAPTCHA_PRIVATE_KEY')
RECAPTCHA_DOMAIN = config('RECAPTCHA_DOMAIN')

EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS').lower() == 'true'
EMAIL_USE_SSL = config('EMAIL_USE_SSL').lower() == 'true'

print('HERE', EMAIL_HOST)

EMAIL_FROM = 'no-reply@winrepo.org'
EMAIL_SUBJECT_PREFIX = 'WiNRepo - '

# Sites settings
SITE_ID = config('SITE_ID', cast=int)
ROBOTS_CACHE_TIMEOUT = 60 * 60 * 24

# Apps settings
CRISPY_TEMPLATE_PACK = 'bootstrap4'

BOOTSTRAP4 = {
    # The URL to the jQuery JavaScript file
    'jquery_url': 'https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js',

    # The Bootstrap base URL
    'base_url': 'https://maxcdn.bootstrapcdn.com/bootstrap/4.3.1/',

    # The complete URL to the Bootstrap CSS file
    # (None means derive it from base_url)
    'css_url':  STATIC_URL + 'css/bootstrap-winrepo.min.css',

    # The complete URL to the Bootstrap JavaScript file
    # (None means derive it from base_url)
    'javascript_url': 'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js'
}

SELECT2_CSS = ''

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ]
}

if DEBUG:
    SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

    LOGGING = {
        'version': 1,
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'filters': ['require_debug_true'],
                'class': 'logging.StreamHandler',
            }
        },
        'loggers': {
            'django.db.backends': {
                'level': 'DEBUG',
                'handlers': ['console'],
            }
        }
    }

if ENV != 'Local':
    SECURE_SSL_REDIRECT = True
