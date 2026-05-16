from django.urls import path
from . import views

urlpatterns = [
    path('', views.base, name='base'),
    path('shop/', views.base, name='shop'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('upload-product/', views.upload_product, name='upload_product'),
    path('search/', views.search_users, name='search_users'),
    path('profile/', views.profile, name='profile'),
    path('messages/', views.messages_view, name='messages'),
    path('send-message/', views.send_message, name='send_message'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('create-post/', views.create_post, name='create_post'),
    path('like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
]