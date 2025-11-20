from django.contrib import admin
from .models import Category, AuthorProfile, Image



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


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
