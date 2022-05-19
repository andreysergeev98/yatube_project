from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .utils import paginator


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()

    page_obj = paginator(request, post_list)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):

    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    page_obj = paginator(request, posts)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)

    post_list = Post.objects.filter(author=user)

    page_obj = paginator(request, post_list)

    post_count = Post.objects.filter(author=user).count()

    context = {
        'author': user,
        'page_obj': page_obj,
        'post_count': post_count,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_count = Post.objects.filter(author=post.author).count()

    context = {
        'post': post,
        'post_count': post_count
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(request.POST or None)
    if form.is_valid():
        author = request.user
        form.instance.author = author
        form.save()
        return redirect('posts:profile', username=author)

    form = PostForm()
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = request.user
    is_edit = True
    if not post.author == author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if not form.is_valid():
        form = PostForm(instance=post)
        context = {
            'form': form,
            'is_edit': is_edit,
            'post_id': post_id
        }
        return render(request, 'posts/create_post.html', context)

    author = request.user
    form.instance.author = author
    obj = form.save(commit=False)
    obj.save()
    return redirect('posts:post_detail', post_id=post_id)
