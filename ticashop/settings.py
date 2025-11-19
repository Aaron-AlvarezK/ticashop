import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-clave-temporal-cambiar-en-produccion')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []

# Apps 
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',    
    'crispy_forms',
    'crispy_bootstrap5',
    
    'apps.usuarios',
    'apps.clientes',
    'apps.productos', 
    'apps.ventas',
    'apps.documentos',
]

# Configuración de usuarios personalizados
AUTH_USER_MODEL = 'usuarios.Usuario'

# Configuración crispy forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ticashop.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'ticashop.wsgi.application'

# Base de datos SQLite para desarrollo rápido
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/images/'
MEDIA_ROOT = BASE_DIR / 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URLs de redirección de login
LOGIN_REDIRECT_URL = '/usuarios/dashboard/'
LOGOUT_REDIRECT_URL = '/usuarios/login/'

# --- AÑADE ESTA LÍNEA ---
# Esta es la URL a la que se redirigirá a los invitados
# cuando intenten hacer una acción que requiera login (como comprar).
LOGIN_URL = 'usuarios:login' 
# --- FIN DE LA LÍNEA ---

# --- CONFIGURACIÓN DE ENVÍO DE EMAIL ---
# (Usa Gmail para desarrollo / universidad)

# COMENTA O BORRA TODAS ESTAS LÍNEAS:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ninovictorvargas@gmail.com'
DEFAULT_FROM_EMAIL = 'TicaShop Latam <ninovictorvargas@gmail.com>'
EMAIL_HOST_PASSWORD = 'hsfx rvbf dfpt ntym'


#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
