from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from GameDB import settings
from games.views import SignUpView

urlpatterns = [
       path('admin/', admin.site.urls),
path('games/', include('games.urls')),
path('accounts/', include('django.contrib.auth.urls')),
path('accounts/signup/', SignUpView.as_view(), name='signup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)