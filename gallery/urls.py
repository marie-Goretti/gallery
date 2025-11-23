from django.urls import path
from . import views
from .views import login_view


urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('publier/', views.upload_image, name='upload_image'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', login_view, name='login'),
    path('api/tags/', views.get_tags_by_category, name='get_tags_by_category'),
]
