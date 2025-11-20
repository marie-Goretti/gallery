from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Image, Category
from .forms import SignUpForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import ImageUploadForm

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
def upload_image(request):
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.author = request.user  # l'utilisateur connecté devient l'auteur
            img.save()
            return redirect('index')  
    else:
        form = ImageUploadForm()

    return render(request, "gallery/upload_image.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('index')