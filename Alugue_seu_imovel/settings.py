import dj_database_url
from pathlib import Path
from django.contrib.messages import constants as messages
import os
from dotenv import load_dotenv

load_dotenv()

# CONFIGURAÇÕES CUSTOMIZADAS DO SITE \/ -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

SITE_NAME = 'Alugue Seu imóvel'
# Coloque aqui a url onde o site ficará hospedado
SITE_URL = 'https://alugue-seu-imovel.onrender.com'
USAR_DB = 1
# /\ 1. SQlite3 Local | 2. PostGreSQL + railway | 3. PostGreSQL + Render.com

# tempo para apagar o form inválido da navbar das sessions (segundos)
TEMPO_SESSION_FORM = 45

# Configurações do gerador de dados fictícios (home.views / home.fakes_test):
# Total a ser criado para cada item / dados iniciais do formulário \/
FICT_QTD = {'qtd_usuario': 5, 'qtd_locatario': 5, 'qtd_imovel_g': 1, 'qtd_imovel': 5, 'qtd_contrato': 4,
            'qtd_pagamento': 10, 'qtd_gasto': 1, 'qtd_nota': 1, 'qtd_sugestao': 1, 'qtd_contr_modelo': 2}

# Tamanho máximo em ‘megabytes’ permitido para envio de imagens para o site, padrão para todos os campos \/
TAMANHO_DAS_IMAGENS_Mb = 4
# Tamanho máximo em ‘megabytes’ permitido para envio de modelos de contratos para o site
TAMANHO_DO_MODELO_Mb = 0.5

# Stripe sistema de pagamentos
pacotes_stripe_precos = ['price_1ODSTJESicPi2hNPMybavcmK', 'price_1ODSUfESicPi2hNPmicDtu1Q',
                         'price_1ODSVeESicPi2hNP1s1p3pWP', 'price_1ODSW8ESicPi2hNPOl3ptDK6']

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
if not STRIPE_SECRET_KEY:
    STRIPE_SECRET_KEY = ('sk_test_51O50TTESicPi2hNPedrL563Ncjc8O9V6b7rSpjHwnCvvxtNBwxKi2Hdp4eyv61'
                         '7Wb1X0Wzp9y7eKetz1bxFxVueg00TGLgmtDA')

STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')
if not STRIPE_ENDPOINT_SECRET:
    STRIPE_ENDPOINT_SECRET = 'whsec_5999d87bf09b37e7a926f2b3ef497b3555990fbf32d3eb37295793c028a10e7f'

# Importante 'número um' (chave de criptografia de CPFs para o banco de dados)
IMPORT_UM = os.getenv('ASI_IMPORT_UM')

# CONFIGURAÇÕES CUSTOMIZADAS DO SITE /\ -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
INSECURE_KEY = 'django-insecure-)t-u^e^z1+z&ni%#(gd2vuc^0uxovq(5k4(w_=r3-2jr^*snqj'
SECRET_KEY = os.environ.get('DJ_SECRET_KEY', INSECURE_KEY)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if DEBUG:
    CSRF_TRUSTED_ORIGINS = ['http://ngrok.io', 'https://3d81-5-62-49-115.ngrok-free.app', ]
else:
    CSRF_TRUSTED_ORIGINS = [SITE_URL, ]

ALLOWED_HOSTS = [SITE_URL.split('//')[1]] + ['*'] if DEBUG else []

X_FRAME_OPTIONS = "SAMEORIGIN"

# Códigos customizados
RECIBOS_CODE = os.environ.get('ASI_recibos')
CONTR_MODEL_CODE = os.environ.get('ASI_contrato-modelo')
CONTRATO_CODE = os.environ.get('ASI_contrato')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',

    # 2FA
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',

    # Ferramentas
    'django_cleanup.apps.CleanupConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'social_django',
    'ckeditor',
    'django_celery_results',
    'django_celery_beat',

    # Site Apps
    'home',
    'financeiro',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'Alugue_seu_imovel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, 'templates/',
                 ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',

                'home.new_context.titulo_pagina',
                'home.new_context.navbar_forms',
                'home.new_context.navbar_notificacoes',
                'home.new_context.ultima_pagina_valida',
            ],
        },
    },
]

WSGI_APPLICATION = 'Alugue_seu_imovel.wsgi.application'

# Configurações da base de dados
if USAR_DB == 1:
    # SQlite3 Local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_admlco32_.sqlite3',
        }
    }
elif USAR_DB == 2:
    # PostGreSQL + Render.com ( with dj-database-url)
    DATABASE_URL = os.environ.get('DB_URL')
    if DATABASE_URL:
        DATABASES = {'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=1800)}
    else:
        DATABASES = {
            'default': {'ENGINE': os.environ.get('DB_ENGINE'),
                        'NAME': os.environ.get('DB_NAME'),
                        'USER': os.environ.get('DB_USER'),
                        'PASSWORD': os.environ.get('DB_PASSWORD'),
                        'HOST': os.environ.get('DB_HOST'),
                        'PORT': os.environ.get('DB_PORT')
                        }
        }

# Redis/Celery Configuration
# No modo de desenvolvimento ele utilizará o servidor local (programa Redis for windows /  Redis-x64-5.0.14.1)
# No modo de produção utilizará o Redis do host

if USAR_DB != 1:
    CELERY_BROKER_URL = 'redis://red-cnico9021fec73cr7r1g:6379'
else:
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXTENDED = True

# Django Celery beat configurations
CELERY_BEAT_SCHERDULLER = 'django_celery_beat.schedulers:DatabaseScheduler'


# Modelo de usuário
AUTH_USER_MODEL = "home.Usuario"

# Password validation
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

LANGUAGE_CODE = 'pt-BR'

TIME_ZONE = 'America/Sao_Paulo'

USE_TZ = False

USE_I18N = True

USE_L10N = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static').replace('\\', '/'), ]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media').replace('\\', '/')

if USAR_DB != 1:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TWO_FACTOR_REMEMBER_COOKIE_AGE = 2592000  # Em segundos: 30 dias
LOGIN_URL = 'two_factor:login'
LOGOUT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'

# configurações do social auth
AUTHENTICATION_BACKENDS = (
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

SOCIAL_AUTH_GOOGLE_KEY = ''
SOCIAL_AUTH_GOOGLE_SECRET = ''

# Configurações do cryspy-forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Substituição do nome das tags do django para as compatíveis com o bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Configurações da biblioteca de redimensionamento das imagens enviadas pelos usuários:
DJANGORESIZED_DEFAULT_SIZE = [1080, None]
DJANGORESIZED_DEFAULT_SCALE = 0.5
DJANGORESIZED_DEFAULT_QUALITY = 75
DJANGORESIZED_DEFAULT_KEEP_META = True
DJANGORESIZED_DEFAULT_FORCE_FORMAT = 'JPEG'
DJANGORESIZED_DEFAULT_FORMAT_EXTENSIONS = {'JPEG': ".jpg"}
DJANGORESIZED_DEFAULT_NORMALIZE_ROTATION = True

# Configurações do editor de modelos
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'height': 620,
        'width': 1280,
        'toolbar_Custom': [
            {'name': 'document', 'items': ['Save', 'NewPage', 'Preview']},
            {'name': 'clipboard', 'items': ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo']},
            {'name': 'editing', 'items': ['Find', 'Replace', '-', 'SelectAll']},
            {'name': 'forms',
             'items': ['Form', 'Checkbox', 'Radio', 'TextField', 'Textarea', 'Select', 'Button', 'ImageButton']},
            {'name': 'insert',
             'items': ['Image', 'Flash', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar', 'PageBreak', 'Iframe']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
            {'name': 'tools', 'items': ['Maximize']},
            '/',
            {'name': 'basicstyles',
             'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl']},
            {'name': 'links', 'items': ['Link', 'Unlink']},
            {'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize']},
        ],
    },
}

# Email
# Ative email_force para usar o console como receptor de emails(modo de testes)
email_force = True
if DEBUG is True and email_force is False:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = os.environ.get('EMAIL_PORT')
    EMAIL_USE_TLS = True
