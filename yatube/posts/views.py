from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User

PAGE_LIMIT = 10


def pagination(request, post_list):
    paginator = Paginator(post_list, PAGE_LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


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

    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)

    context = {
        'post': post,
    }
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
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
    form = PostForm(request.POST or None, instance=post)

    if post.author != request.user:
        return redirect('posts:index')

    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post.id)

    return render(request, template, {'form': form, 'is_edit': True})
