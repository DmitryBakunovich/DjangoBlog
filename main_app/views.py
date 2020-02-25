from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import random

from .forms import ArticleForm, CommentForm
from .models import Article, Comment, Like, CustomUser


def main_page(request):
    AMOUNT_LAST_COMMENTS = 4
    last_comments = Comment.objects.order_by('-date')[:AMOUNT_LAST_COMMENTS]
    all_articles = Article.objects.annotate(
        like_count=Count('like',filter=Q(like__is_liked=True), distinct=True),
        comment_count=Count('comment', distinct=True)
    ).order_by('-date')
    ids_for_articles = Article.objects.values_list('id', flat=True)
    ids_for_articles = list(ids_for_articles)
    AMOUNT_RANDOM_ARTICLES = 3
    random_ids_for_article = random.sample(ids_for_articles, AMOUNT_RANDOM_ARTICLES)
    main_article = Article.objects.annotate(
        like_count=Count('like',filter=Q(like__is_liked=True), distinct=True),
        comment_count=Count('comment', distinct=True)
    ).filter(id__in=random_ids_for_article)
    paginator = Paginator(all_articles, 8)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    return render(
        request,
        'main_app/basic_page.html',
        {
            'main_article': main_article[0],
            'main_articles': main_article[1:3],
            'articles': articles,
            'comment': last_comments,
        },
    )


# page article with comments
def page_article(request, article_id=1):
    AMOUNT_LAST_ARTICLES = 2
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article_id = article_id
            comment.author_id = request.user.id
            comment.date = timezone.now()
            comment.save()
            return redirect('article_detail', article_id=article_id)
    else:
        form = CommentForm()

    all_likes_in_article = Like.objects.filter(article_id=article_id).count()
    if all_likes_in_article:
        likes = Like.objects.filter(article_id=article_id, is_liked=True).count()
        like_percent = likes*100/all_likes_in_article
        dislikes = Like.objects.filter(article_id=article_id, is_liked=False).count()
        dislike_percent = dislikes*100/all_likes_in_article
    else:
        like_percent = 0
        dislike_percent = 0
    return render(
        request,
        'main_app/article.html',
        {
            'form': form,
            'last_articles': Article.objects.all().filter(author_id=request.user.id)[:AMOUNT_LAST_ARTICLES],
            'article': Article.objects.get(id=article_id),
            'is_liked': Like.objects.filter(article_id=article_id, user_id=request.user.id),
            'all_likes': Like.objects.filter(article_id=article_id, is_liked=True).count(),
            'marks': Like.objects.filter(article_id=article_id).values('is_liked').annotate(count=Count('is_liked')).order_by('-is_liked'),
            'like_percent': round(like_percent),
            'dislike_percent': round(dislike_percent),
            'comment': Comment.objects.filter(article_id=article_id).order_by('-date'),
        }
    )


def add_like(request, article_id):
    Like.objects.create(user_id=request.user.id, article_id=article_id, is_liked=True)
    return redirect(
        'article_detail',
        article_id=article_id
    )


def add_dislike(request, article_id):
    Like.objects.create(user_id=request.user.id, article_id=article_id, is_liked=False)
    return redirect(
        'article_detail',
        article_id=article_id
    )


def user_profile(request, user_id=1):
    user = CustomUser.objects.get(id=user_id)
    return render(
        request,
        'main_app/user_profile.html',
        {
            'is_my_profile': request.user.id == user.id,
            'user_article_count': Article.objects.filter(author_id=user_id).count(),
            'user_comment_count': Comment.objects.filter(author_id=user_id).count(),
            'user': user,
        }
    )


def edit_user(request):
    user_id = request.user.id
    user = CustomUser.objects.get(id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        if request.FILES.get('image'):
            user.avatar = request.FILES.get('image')
        user.save()
    return render(
        request,
        'main_app/edit_user_profile.html',
        {
            'user_article_count': Article.objects.filter(author_id=user_id).count(),
            'user_comment_count': Comment.objects.filter(author_id=user_id).count(),
            'user': user,
        },
    )


def article_created_by_user(request, user_id=1):
    AMOUNT_LAST_COMMENTS = 4
    last_comments = Comment.objects.order_by('-date')[0:AMOUNT_LAST_COMMENTS]
    all_article = Article.objects.annotate(
        like_count=Count('like', filter=Q(like__is_liked=True), distinct=True),
        comment_count=Count('comment', distinct=True)
    ).filter(author_id=user_id).order_by('-date')
    paginator = Paginator(all_article, 8)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    return render(
        request,
        'main_app/articles_created_by_user.html',
        {
            'articles': articles,
            'comment': last_comments,
            'user': CustomUser.objects.get(id=user_id),
        }
    )


def new_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author_id = request.user.id
            article.date = timezone.now()
            article.save()
            return redirect(
                'article_detail',
                article_id=article.id
            )
    else:
        form = ArticleForm()
    return render(
        request,
        'main_app/article_edit.html',
        {
            'form': form,
            'type': 'CREATE',
        }
    )


def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    form = ArticleForm(request.POST or None, request.FILES or None, instance=article)
    if request.method == 'POST':
        article.title = request.POST.get('title')
        article.text = request.POST.get('text')
        article.short_description = request.POST.get('short_description')
        if request.FILES.get('image'):
            article.image = request.FILES.get('image')
        article.save()
    return render(
        request,
        'main_app/article_edit.html',
        {
            'form': form,
            'article': article,
            'type': 'UPDATE',
        }
    )


def delete_article(request, article_id):
    article = Article.objects.get(id=article_id)
    article.delete()
    return redirect('/')
