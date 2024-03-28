from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from two_factor.urls import urlpatterns as tf_urls
from django.contrib.auth import views as auth_view

urlpatterns = [
    path('', include(tf_urls)),
    path('admin/', admin.site.urls),
    path('oauth/', include('social_django.urls', namespace='social')),

    path('', include('core.urls', namespace='core')),
    path('', include('financeiro.urls', namespace='financeiro')),

    path('password_reset/',
         auth_view.PasswordResetView.as_view(html_email_template_name='registration/password_reset_email.html',
                                             template_name='password_reset/password_reset_form.html', ),
         name="password_reset"),
    path('password_reset/done/',
         auth_view.PasswordResetDoneView.as_view(template_name='password_reset/password_reset_done.html'),
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
         auth_view.PasswordResetConfirmView.as_view(template_name='password_reset/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_view.PasswordResetCompleteView.as_view(template_name='password_reset/password_reset_complete.html'),
         name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
