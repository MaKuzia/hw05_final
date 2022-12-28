from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from core.views import get_post
from posts.utils import paginate_posts

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    context = {
        'page_obj': paginate_posts(request, Post.objects.all()),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts_group = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginate_posts(request, posts_group),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.all()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': paginate_posts(request, user_posts),
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    comments = get_post(post_id).comments.all()
    context = {
        'post': get_post(post_id),
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,)
    if form.is_valid():
        post = form.save(False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    current_post = get_post(post_id)
    if request.user != current_post.author:
        return redirect('posts:post_detail', current_post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=current_post,
    )
    if form.is_valid():
        current_post.save()
        return redirect('posts:post_detail', current_post.pk)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_post(post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    authors = request.user.follower.values_list('author', flat=True)
    posts = Post.objects.filter(author__in=authors)
    context = {
        'page_obj': paginate_posts(request, posts),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if username != request.user.username and not Follow.objects.filter(
        user=request.user, author=User.objects.get(username=username)
    ).exists():
        Follow.objects.create(
            user=request.user,
            author=User.objects.get(username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).delete()
    return redirect('posts:profile', username)
