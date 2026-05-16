from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from .models import UserProfile, Friendship, Post, Like, Comment, Message
from .forms import UserProfileForm, CustomUserCreationForm, CustomAuthenticationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Login failed. Please check your username and password.')
    else:
        form = CustomAuthenticationForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/')


def base(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    return render(request, 'services.html')


def shop(request):
    # Simple static product list for the shop page; replace with DB models later
    products = [
        {'id': 1, 'name': 'Leather Handbag', 'price': '79.99', 'description': 'Stylish leather handbag perfect for everyday use.'},
        {'id': 2, 'name': 'Classic Sneakers', 'price': '59.99', 'description': 'Comfortable and fashionable sneakers.'},
        {'id': 3, 'name': 'Vintage Sunglasses', 'price': '29.99', 'description': 'UV-protected retro sunglasses.'},
        {'id': 4, 'name': 'Wool Scarf', 'price': '19.99', 'description': 'Warm and soft scarf for chilly days.'},
    ]

    return render(request, 'shop.html', {'products': products})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    user_posts = Post.objects.filter(author=request.user)
    posts_count = user_posts.count()
    follower_count = Friendship.objects.filter(following=request.user).count()
    following_count = Friendship.objects.filter(follower=request.user).count()

    return render(request, 'profile.html', {
        'form': form,
        'user_profile': user_profile,
        'user_posts': user_posts[:9],
        'posts_count': posts_count,
        'follower_count': follower_count,
        'following_count': following_count,
    })


@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = []
    if query:
        users = UserProfile.objects.filter(
            Q(user__username__icontains=query) | Q(user__first_name__icontains=query)
        ).exclude(user=request.user)[:20]
    
    return render(request, 'search_users.html', {'users': users, 'query': query})


@login_required
def user_detail(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    user_profile, _ = UserProfile.objects.get_or_create(user=target_user)
    user_posts = Post.objects.filter(author=target_user)
    
    is_following = Friendship.objects.filter(follower=request.user, following=target_user).exists()
    
    posts_count = user_posts.count()
    follower_count = Friendship.objects.filter(following=target_user).count()
    following_count = Friendship.objects.filter(follower=target_user).count()
    
    return render(request, 'user_detail.html', {
        'target_user': target_user,
        'user_profile': user_profile,
        'user_posts': user_posts[:9],
        'is_following': is_following,
        'posts_count': posts_count,
        'follower_count': follower_count,
        'following_count': following_count,
    })


@login_required
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if request.user == target_user:
        messages.error(request, "You can't follow yourself!")
        return redirect('user_detail', user_id=user_id)
    
    friendship = Friendship.objects.filter(follower=request.user, following=target_user)
    
    if friendship.exists():
        friendship.delete()
        messages.success(request, f"Unfollowed {target_user.username}")
    else:
        Friendship.objects.create(follower=request.user, following=target_user)
        messages.success(request, f"Following {target_user.username}")
    
    return redirect('user_detail', user_id=user_id)


@login_required
def create_post(request):
    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        image = request.FILES.get('image', None)
        
        if caption or image:
            Post.objects.create(author=request.user, caption=caption, image=image)
            messages.success(request, 'Post created successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please add a caption or image.')
    
    return render(request, 'create_post.html')


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like = Like.objects.filter(post=post, user=request.user)
    
    if like.exists():
        like.delete()
    else:
        Like.objects.create(post=post, user=request.user)
    
    return redirect(request.META.get('HTTP_REFERER', 'profile'))


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(post=post, author=request.user, content=content)
            messages.success(request, 'Comment added!')
    
    return redirect(request.META.get('HTTP_REFERER', 'profile'))


@login_required
def messages_view(request):
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')

    conversations = []
    seen_users = set()

    for msg in all_messages:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user.id in seen_users:
            continue

        other_profile, _ = UserProfile.objects.get_or_create(user=other_user)
        unread_count = Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).count()

        conversations.append({
            'other_user': other_user,
            'other_profile': other_profile,
            'last_message': msg.content,
            'last_date': msg.created_at,
            'unread_count': unread_count,
        })
        seen_users.add(other_user.id)

    selected_user_id = request.GET.get('user_id')
    messages_list = []
    selected_user = None

    if selected_user_id:
        selected_user = get_object_or_404(User, id=selected_user_id)
        messages_list = Message.objects.filter(
            Q(sender=request.user, receiver=selected_user) |
            Q(sender=selected_user, receiver=request.user)
        ).order_by('created_at')

        Message.objects.filter(sender=selected_user, receiver=request.user).update(is_read=True)

    return render(request, 'messages.html', {
        'conversations': conversations,
        'messages': messages_list,
        'selected_user': selected_user,
    })


@login_required
def send_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content', '').strip()

        if receiver_id and content:
            receiver = get_object_or_404(User, id=receiver_id)
            msg = Message.objects.create(sender=request.user, receiver=receiver, content=content)
            messages.success(request, 'Message sent!')
            # If request is AJAX, return JSON so client can append without full reload
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': msg.id,
                    'content': msg.content,
                    'sender_id': request.user.id,
                    'sender_username': request.user.username,
                    'created_at': msg.created_at.strftime('%b %d, %H:%M'),
                }, status=201)
            return redirect(f"{reverse('messages')}?user_id={receiver_id}#messages-chat")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Receiver and content required.'}, status=400)

    return redirect('messages')
def shop(request):
    return render(request, 'shop.html')
from .models import UserProfile, Friendship, Post, Like, Comment, Message, Product

def base(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'base.html', {'products': products})
from .models import UserProfile, Friendship, Post, Like, Comment, Message, Product
from .forms import UserProfileForm, CustomUserCreationForm, CustomAuthenticationForm, ProductForm

def base(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'base.html', {'products': products})

@login_required
def upload_product(request):
    if not request.user.is_superuser:
        return redirect('/')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product uploaded successfully!')
            return redirect('/')
    else:
        form = ProductForm()
    return render(request, 'upload_product.html', {'form': form})
from .models import UserProfile, Friendship, Post, Like, Comment, Message, Product, Cart, CartItem

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart!')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})


@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return redirect('cart')