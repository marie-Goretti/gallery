from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SignUpForm, ImageUploadForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Image, Category, Tag
from django.db.models import Count, Q
from .models import Image, Category, Tag, ImageLike, ImageView, Comment
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from django.utils import timezone


def index(request):
    q = request.GET.get("q")
    images = Image.objects.all()

    if q:
        images = images.filter(title__icontains=q)

    categories = Category.objects.all()

    return render(request, "gallery/index.html", {
        "images": images,
        "categories": categories,
        "current_category": None,   # Aucune catégorie active ici
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connexion automatique après inscription
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'gallery/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'gallery/login.html')

def category_view(request, slug):
    category = Category.objects.get(slug=slug)
    images = Image.objects.filter(category=category)
    categories = Category.objects.all()

    return render(request, "gallery/index.html", {   
        "images": images,
        "categories": categories,
        "current_category": slug,   
    })


@login_required
def get_tags_by_category(request):
    """API pour récupérer les tags avec recherche globale"""
    search = request.GET.get('search', '')
    category_id = request.GET.get('category_id')
    
    tags = Tag.objects.select_related('category')
    
    # Filtrer par catégorie si spécifiée
    if category_id:
        tags = tags.filter(category_id=category_id)
    
    # Filtrer par recherche
    if search:
        tags = tags.filter(name__icontains=search)
    
    # Limiter à 20 résultats
    tags = tags[:20]
    
    tags_list = [{
        'id': tag.id, 
        'name': tag.name,
        'category': tag.category.name
    } for tag in tags]
    
    return JsonResponse({'tags': tags_list})


@login_required
def upload_image(request):
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.author = request.user
            img.save()
            
            # Récupérer les tags sélectionnés
            tags_ids = request.POST.get('tags_ids', '')
            if tags_ids:
                tag_ids_list = [int(tid) for tid in tags_ids.split(',') if tid.strip().isdigit()]
                tags = Tag.objects.filter(id__in=tag_ids_list)
                img.tags.set(tags)
                
                # Assigner automatiquement la catégorie basée sur le premier tag
                if tags.exists():
                    img.category = tags.first().category
                    img.save(update_fields=['category'])
            
            messages.success(request, 'Image publiée avec succès !')
            return redirect('index')
    else:
        form = ImageUploadForm()

    return render(request, "gallery/upload_image.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('index')



def get_client_ip(request):
    """Récupérer l'IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def image_detail(request, slug):
    """Page de détail d'une image"""
    image = get_object_or_404(Image, slug=slug)
    
    # Enregistrer une vue (une seule par utilisateur/IP par image)
    ip_address = get_client_ip(request)
    if request.user.is_authenticated:
        ImageView.objects.get_or_create(image=image, user=request.user)
    else:
        # Pour les utilisateurs non connectés, une vue par IP
        ImageView.objects.get_or_create(image=image, ip_address=ip_address)
    
    # Récupérer les commentaires
    comments = image.comments.select_related('author').all()
    
    # Trouver des images similaires
    similar_images = Image.objects.filter(
        category=image.category
    ).exclude(id=image.id)
    
    # Ajouter les images avec des tags en commun
    image_tags = image.tags.all()
    if image_tags.exists():
        # Utiliser Q objects pour combiner les conditions
        from django.db.models import Q
        
        similar_images = Image.objects.filter(
            Q(category=image.category) | Q(tags__in=image_tags)
        ).exclude(id=image.id).distinct()
    
    # Limiter à 6 images similaires et annoter avec le nombre de likes
    similar_images = similar_images.annotate(
        likes_count=Count('likes')
    ).order_by('-likes_count', '-created_at')[:6]
    
    context = {
        'image': image,
        'comments': comments,
        'similar_images': similar_images,
        'is_liked': image.is_liked_by(request.user),
        'likes_count': image.get_likes_count(),
        'views_count': image.get_views_count(),
        'comments_count': image.get_comments_count(),
    }
    
    return render(request, 'gallery/image_detail.html', context)


@require_POST
@login_required
def toggle_like(request, slug):
    """Toggle like/unlike d'une image"""
    image = get_object_or_404(Image, slug=slug)
    
    like, created = ImageLike.objects.get_or_create(image=image, user=request.user)
    
    if not created:
        # Le like existait déjà, on le supprime
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': image.get_likes_count()
    })


@require_POST
@login_required
def add_comment(request, slug):
    """Ajouter un commentaire"""
    image = get_object_or_404(Image, slug=slug)
    content = request.POST.get('comment-content', '').strip()
    
    if content:
        comment = Comment.objects.create(
            image=image,
            author=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'author': comment.author.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%d/%m/%Y à %H:%M'),
                'can_delete': True
            },
            'comments_count': image.get_comments_count()
        })
    
    return JsonResponse({'success': False, 'error': 'Commentaire vide'})


@require_POST
@login_required
def delete_comment(request, comment_id):
    """Supprimer un commentaire"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérifier que l'utilisateur est l'auteur
    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    
    image_slug = comment.image.slug
    comments_count = comment.image.get_comments_count() - 1
    comment.delete()
    
    return JsonResponse({
        'success': True,
        'comments_count': comments_count
    })


@login_required
def profile_view(request):
    """Page de profil utilisateur avec statistiques"""
    user = request.user
    profile = user.profile
    
    # Images de l'utilisateur
    user_images = Image.objects.filter(author=user).order_by('-created_at')
    
    # Statistiques globales
    total_images = user_images.count()
    total_views = sum(img.get_views_count() for img in user_images)
    total_likes = sum(img.get_likes_count() for img in user_images)
    total_comments = sum(img.get_comments_count() for img in user_images)
    
    # Statistiques des 30 derniers jours
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    recent_images = user_images.filter(created_at__gte=thirty_days_ago)
    recent_images_count = recent_images.count()
    
    # Calcul des likes des 30 derniers jours
    recent_likes = ImageLike.objects.filter(
        image__author=user,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Calcul des commentaires des 30 derniers jours
    recent_comments = Comment.objects.filter(
        image__author=user,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Calcul des vues des 30 derniers jours
    recent_views = ImageView.objects.filter(
        image__author=user,
        viewed_at__gte=thirty_days_ago
    ).count()
    
    # Calcul des followers (nombre de personnes qui ont liké vos images)
    unique_likers = ImageLike.objects.filter(
        image__author=user
    ).values('user').distinct().count()
    
    # Calcul de la croissance (simulée pour l'exemple)
    # Vous pouvez améliorer cela en comparant avec les 30 jours précédents
    images_growth = 0
    if total_images > 0:
        old_images = user_images.filter(created_at__lt=thirty_days_ago).count()
        if old_images > 0:
            images_growth = ((recent_images_count - old_images) / old_images) * 100
    
    likes_growth = 0
    if total_likes > 0:
        old_likes = ImageLike.objects.filter(
            image__author=user,
            created_at__lt=thirty_days_ago
        ).count()
        if old_likes > 0:
            likes_growth = ((recent_likes - old_likes) / old_likes) * 100
    
    context = {
        'profile': profile,
        'user_images': user_images,
        'total_images': total_images,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'recent_images_count': recent_images_count,
        'recent_likes': recent_likes,
        'recent_comments': recent_comments,
        'recent_views': recent_views,
        'unique_likers': unique_likers,
        'images_growth': round(images_growth, 1),
        'likes_growth': round(likes_growth, 1),
    }
    
    return render(request, 'gallery/profile.html', context)


@login_required
def edit_profile(request):
    """Éditer le profil utilisateur"""
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        # Mise à jour du nom d'utilisateur
        new_username = request.POST.get('username', '').strip()
        if new_username and new_username != user.username:
            # Vérifier si le nom d'utilisateur est déjà pris
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, 'Ce nom d\'utilisateur est déjà pris.')
                return redirect('profile')
            user.username = new_username
        
        # Mise à jour de l'email
        user.email = request.POST.get('email', '')
        profile.bio = request.POST.get('bio', '')
        
        # Gestion de l'avatar
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        user.save()
        profile.save()
        
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('profile')
    
    return redirect('profile')


@login_required
def delete_image(request, slug):
    """Supprimer une image"""
    image = get_object_or_404(Image, slug=slug, author=request.user)
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image supprimée avec succès !')
        return redirect('profile')
    
    return render(request, 'gallery/confirm_delete.html', {'image': image})


@login_required
def edit_image(request, slug):
    """Modifier une image"""
    image = get_object_or_404(Image, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            img = form.save()
            
            # Mise à jour des tags
            tags_ids = request.POST.get('tags_ids', '')
            if tags_ids:
                tag_ids_list = [int(tid) for tid in tags_ids.split(',') if tid.strip().isdigit()]
                tags = Tag.objects.filter(id__in=tag_ids_list)
                img.tags.set(tags)
                
                if tags.exists():
                    img.category = tags.first().category
                    img.save(update_fields=['category'])
            
            messages.success(request, 'Image modifiée avec succès !')
            return redirect('profile')
    else:
        form = ImageUploadForm(instance=image)
    
    return render(request, 'gallery/edit_image.html', {
        'form': form, 
        'image': image
    })