from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_room, name='create_room'),
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('room/<int:room_id>/send/', views.send_message, name='send_message'),
    path('room/<int:room_id>/messages/', views.get_messages, name='get_messages'),
    path('room/<int:room_id>/diary/', views.diary_entry, name='diary_entry'),
    path('room/<int:room_id>/schedule/', views.schedule_message, name='schedule_message'),
    path('stickers/upload/', views.upload_sticker, name='upload_sticker'),
    path('room/<int:room_id>/invite/', views.generate_invite, name='generate_invite'),
    path('join/<str:invite_code>/', views.join_room, name='join_room'),
    path('accounts/logout/', views.logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 