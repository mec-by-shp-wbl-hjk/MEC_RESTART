from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from django.conf import settings
from django.urls import include
from MECboard import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.list, name='list'),
    path('join/', views.join, name='join'),
    path('accounts/', include('allauth.urls')),
    path('login/', views.login_check, name='login'),
    path('logout/', views.logout, name='logout'),
    path('write', views.write),
    path('insert', views.insert),
    path('download', views.download),
    path('detail', views.detail),
    path('update', views.update),
    path('delete', views.delete),
    path('reply_insert', views.reply_insert),
    path('update_page', views.update_page),
    path('reply_rating', views.reply_rating),
    path('reply_update', views.reply_update),
    path('reply_delete', views.reply_delete),
    path('reply_update_page', views.reply_update_page),
    path('evidence_insert', views.evidence_insert),
    path('create_profile', views.create_profile),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

