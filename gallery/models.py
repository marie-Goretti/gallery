from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image as PilImage
import os
from django.db.models.signals import post_save
from django.dispatch import receiver

def image_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    return f"gallery/{instance.author.username}/{instance.slug or slugify(name)}{ext.lower()}"

# validators
def validate_image_file_extension(file):
    valid_mimetypes = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if hasattr(file, 'content_type'):
        if file.content_type not in valid_mimetypes:
            raise ValidationError("Format de fichier non supporté. Utilise JPG, PNG, GIF ou WEBP.")
    else:
        # fallback : vérifier l'extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            raise ValidationError("Format de fichier non supporté (extension).")

def validate_image_size(file):
    max_bytes = 5 * 1024 * 1024  # 5 MB
    if file.size > max_bytes:
        raise ValidationError("Le fichier est trop lourd (max 5 MB).")

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=80, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="tags")

    class Meta:
        unique_together = ['name', 'category']  # Un tag unique par catégorie
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
class AuthorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Créer automatiquement un profil AuthorProfile lors de la création d'un utilisateur"""
    if created:
        AuthorProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarder le profil lorsque l'utilisateur est sauvegardé"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Si le profil n'existe pas encore (cas des anciens utilisateurs)
        AuthorProfile.objects.get_or_create(user=instance)

class Image(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="images")
    tags = models.ManyToManyField(Tag, blank=True, related_name="images")  # NOUVEAU

    image = models.ImageField(upload_to=image_upload_path, validators=[validate_image_file_extension, validate_image_size])

    created_at = models.DateTimeField(auto_now_add=True)

    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # créer/mettre à jour le slug
        if not self.slug:
            base = self.title or "image"
            unique = slugify(base)
            # s'assurer d'unicité simple (peut être améliorée)
            counter = 1
            orig = unique
            while Image.objects.filter(slug=unique).exclude(pk=self.pk).exists():
                unique = f"{orig}-{counter}"
                counter += 1
            self.slug = unique

        super().save(*args, **kwargs)  # sauvegarde initiale pour obtenir le fichier

        # ouvrir l'image physiquement pour extraire métadonnées
        try:
            img_path = self.image.path
            img = PilImage.open(img_path)
            self.width, self.height = img.size
            self.file_size = os.path.getsize(img_path)
            # Optionnel : redimensionner si trop grande (ex : maxi 4000x4000)
            max_w, max_h = 4000, 4000
            if self.width > max_w or self.height > max_h:
                img.thumbnail((max_w, max_h), PilImage.ANTIALIAS)
                img.save(img_path)
                self.width, self.height = img.size
                self.file_size = os.path.getsize(img_path)
            super().save(update_fields=['width', 'height', 'file_size'])
        except Exception:
            pass

    def __str__(self):
        return self.title
