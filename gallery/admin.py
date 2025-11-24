from django.contrib import admin
from .models import Category,Tag, AuthorProfile, Image, ImageLike, ImageView, Comment
from django.contrib import admin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug']
    list_filter = ['category']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "bio")
    search_fields = ("user__username", "bio")
    list_filter = ("user",)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "created_at", "file_size")
    search_fields = ("title", "description", "author__username")
    list_filter = ("category", "author", "created_at")

    readonly_fields = ("width", "height", "file_size", "slug", "created_at")

    # pour auto-compléter le slug quand tu tapes un titre
    prepopulated_fields = {"slug": ("title",)}

    # pour afficher certains champs dans le formulaire de modification
    fieldsets = (
        ("Informations générales", {
            "fields": ("title", "slug", "description", "author", "category")
        }),
        ("Image", {
            "fields": ("image",)
        }),
        ("Métadonnées (automatique)", {
            "fields": ("width", "height", "file_size", "created_at"),
        }),
    )


@admin.register(ImageLike)
class ImageLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'image', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'image__title']

@admin.register(ImageView)
class ImageViewAdmin(admin.ModelAdmin):
    list_display = ['image', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username', 'image__title', 'ip_address']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'image', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'image__title', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'