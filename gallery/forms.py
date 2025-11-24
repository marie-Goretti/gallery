from django import forms
import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from .models import Image, Category
from django import forms
from .models import Image, Tag, Category

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'captcha')
    
    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        # Vérifications regex
        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r"[a-z]", password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r"[0-9]", password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
        if len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au minimum 8 caractères.")

        return password
    

class ImageUploadForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,  # MODIFIÉ : Non obligatoire
        empty_label="Choisir une catégorie (optionnel)...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez pour rechercher des tags...',
            'id': 'tags-input'
        }),
        help_text='Recherchez et sélectionnez des tags correspondant à votre image'
    )

    class Meta:
        model = Image
        fields = ['title', 'description', 'category', 'image']