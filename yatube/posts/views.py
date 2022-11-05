from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

PAGE_LIMIT = 10


def pagination(request, post_list):
    paginator = Paginator(post_list, PAGE_LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20, key_prefix="index_page")
def index(request):
    template = 'posts/index.html'

    post_list = Post.objects.select_related("group")

    page_obj = pagination(request=request, post_list=post_list)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()

    page_obj = pagination(request=request, post_list=post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    page_obj = pagination(request=request, post_list=author.posts.all())

    following = Follow.objects.filter(author=author)
    context = {
        'following': following,
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.save()
        return redirect("posts:profile", request.user)

    context = {
        'form': form,
        'is_edit': False}

    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    posts = Post.objects.select_related('group')
    post = get_object_or_404(posts, id=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }

    return render(request, template, context)


@login_required
def post_delete(request, post_id):
    posts = Post.objects.select_related('group')
    post = get_object_or_404(posts, id=post_id)
    if post.author != request.user:
        return redirect('posts:index')
    post.delete()
    return redirect(f'/profile/{post.author.username}')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('posts:add_comment', post_id=post_id)

    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    author_querry = Follow.objects.filter(user=request.user)
    author_values_list = author_querry.values_list('author')
    post_list = Post.objects.filter(author_id__in=author_values_list)

    page_obj = pagination(request=request, post_list=post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(f'/profile/{username}/')
    Follow.objects.create(
        user=request.user,
        author=author
    )
    return redirect(f'/profile/{username}/')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, author=author)
    follow.delete()
    return redirect(f'/profile/{username}')
