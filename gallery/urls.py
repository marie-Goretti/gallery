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
    path('image/<slug:slug>/', views.image_detail, name='image_detail'),
    path('image/<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    path('image/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('image/<slug:slug>/edit/', views.edit_image, name='edit_image'),
    path('image/<slug:slug>/delete/', views.delete_image, name='delete_image'),
]
