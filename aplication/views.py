from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
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


def base(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    return render(request, 'services.html')

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
    user_profile = UserProfile.objects.get(user=target_user)
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
    # Get all unique conversations
    sent_messages = Message.objects.filter(sender=request.user)
    received_messages = Message.objects.filter(receiver=request.user)
    
    # Get list of people user has messaged
    conversations = []
    seen_users = set()
    
    for msg in sent_messages.order_by('-created_at'):
        if msg.receiver.id not in seen_users:
            conversations.append(msg)
            seen_users.add(msg.receiver.id)
    
    for msg in received_messages.order_by('-created_at'):
        if msg.sender.id not in seen_users:
            conversations.append(msg)
            seen_users.add(msg.sender.id)
    
    conversations.sort(key=lambda x: x.created_at, reverse=True)
    
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
        'selected_user_id': selected_user_id,
        'selected_user': selected_user,
    })


@login_required
def send_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content', '').strip()
        
        if receiver_id and content:
            receiver = get_object_or_404(User, id=receiver_id)
            Message.objects.create(sender=request.user, receiver=receiver, content=content)
            messages.success(request, 'Message sent!')
            return redirect('messages')
    
    return redirect('messages')
