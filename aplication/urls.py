from django.urls import path
from . import views

urlpatterns = [
    path('', views.base, name='base'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('shop/', views.shop, name='shop'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.search_users, name='search_users'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('user/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('messages/', views.messages_view, name='messages'),
    path('message/send/', views.send_message, name='send_message'),
]
