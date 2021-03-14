"""
Django settings for mvapi project.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from django.http.request import RAISE_ERROR

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_URL = os.environ['SITE_URL']
DEBUG = os.environ['DJANGO_DEBUG'] == 'True'
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = os.environ['DJANGO_ALLOWED_HOSTS'].split(',')
MAX_NUM_GRADES = int(os.environ['MAX_NUM_GRADES'])
LANGUAGE_AVAILABLE = os.environ['LANGUAGE_AVAILABLE']
DEFAULT_LANGUAGE = "en"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'corsheaders',
    'election'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware'
]

CORS_ORIGIN_ALLOW_ALL=True

ROOT_URLCONF = 'mvapi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mvapi.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
	
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

################################################################################
#                                                                              #
#                       MAIL SETTINGS                                          #
#                                                                              #
################################################################################
if os.environ['EMAIL_USE_TLS'] in ("True", "true", "on", "1"):
    EMAIL_USE_TLS = True
else:
    EMAIL_USE_TLS = False

EMAIL_TYPE = os.environ['EMAIL_TYPE']
if EMAIL_TYPE == "API":
    #To use the Mailgun's API
    EMAIL_API_KEY=os.environ['EMAIL_API_KEY']
    EMAIL_API_DOMAIN=os.environ['EMAIL_API_DOMAIN']
    DEFAULT_FROM_EMAIL=os.environ['DEFAULT_FROM_EMAIL']
    EMAIL_SKIP_VERIFICATION=os.environ['EMAIL_SKIP_VERIFICATION']

elif EMAIL_TYPE == "SMTP":
    #To use with a SMTP service
    EMAIL_BACKEND=os.environ['EMAIL_BACKEND']
    EMAIL_HOST_USER=os.environ['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD=os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_PORT=os.environ['EMAIL_PORT']
    EMAIL_HOST=os.environ['EMAIL_HOST']

else:
    raise ValueError('API and SMTP are only available')