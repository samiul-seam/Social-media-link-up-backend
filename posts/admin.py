from django.contrib import admin
from .models import Post, PostMedia, Like, Comment, Reply


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    show_change_link = True


class ReplyInline(admin.TabularInline):
    model = Reply
    extra = 1
    show_change_link = True


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'caption', 'created_at']
    search_fields = ['caption', 'user__username']
    inlines = [PostMediaInline, CommentInline]


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'file']
    search_fields = ['post__caption', 'post__user__username']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'user']
    search_fields = ['post__caption', 'user__username']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'user', 'content', 'created_at']
    search_fields = ['post__caption', 'user__username', 'content']
    inlines = [ReplyInline]


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'comment', 'user', 'content', 'created_at']
    search_fields = ['comment__content', 'user__username', 'content']