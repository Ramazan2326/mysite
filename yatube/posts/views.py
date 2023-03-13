from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User
from .paginator_mod import paginate_page
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required


def index(request):
    """ Creates necessary link. """

    posts = Post.objects.all()
    page_obj = paginate_page(posts, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """ Sorts posts in appropriate groups. """

    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    page_obj = paginate_page(posts, request)
    context = {'group': group, 'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """ User's posts in his/her profile. """

    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginate_page(posts, request)
    context = {
        "author": author,
        'page_obj': page_obj
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """ Special information about post. """

    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    count_post = post.author.posts.count()
    comments = post.comments.select_related('author')
    context = {
        'author': post.author,
        'post': post,
        'count_post': count_post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """ Gives us possibility to create new post. """

    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    """ Gives us possibility to edit post. """
    post_object = get_object_or_404(
        Post,
        id=post_id,
        author=request.user
    )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post_object
    )
    if form.is_valid():
        form.save()
        if post_object.author == request.user:
            return redirect('posts:post_edit', post_id)
        if post_object.author != request.user:
            return redirect('posts/post_detail.html', post_id)
    context = {
        'form': form,
        'True': True,
        'post': post_object,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(
        request,
        'posts/includes/comments.html',
        {
            'form': form,
            'post': post,
        }
    )
