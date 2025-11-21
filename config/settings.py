import os
from dotenv import load_dotenv 

# ----------------------------------------------------------------------
# API ANAHTARI GÜVENLİK VE YÜKLEME KISMI
# Bu kodun dosyanın en başında olması KRİTİKTİR.
# ----------------------------------------------------------------------

# .env dosyasını yükle
# Anahtarınızı .env dosyasına yazdıysanız, bu kod onu çekecektir.
load_dotenv()

# Anahtarı bir Python değişkenine çekin
# Not: Sizin verdiğiniz anahtar doğrudan kodda GÖSTERİLMEMELİDİR. 
# Bu yüzden kod sadece .env dosyasından çekiyor.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# Eğer anahtar .env dosyasında bulunamazsa programı durdur
if not GEMINI_API_KEY:
    # Eğer test için anahtarı buraya koymak isterseniz (önerilmez), 
    # aşağıdaki satırın yorumunu kaldırıp değeri güncelleyebilirsiniz:
    # GEMINI_API_KEY = "AIzaSyBymy2Ptk4hypZSRO8ertNQQbQ0JVNDDYQ" 
    raise EnvironmentError("HATA: GEMINI_API_KEY, .env dosyasında bulunamadı!")

# ----------------------------------------------------------------------
# DJANGO TEMEL AYARLARI
# ----------------------------------------------------------------------

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7=ql&s4ya46q5!6z@9y5yp8ngp^wbpn@1r5_$$l%7$bx+zh=3c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ogrenme', # Sizin uygulamanız
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Giriş ve Çıkış sonrası yönlendirmeler (İsteğe bağlı ama iyi uygulama)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'