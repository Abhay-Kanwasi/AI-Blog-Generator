from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.user_login, name='user_login'),
    path('signup/', views.user_signup, name='user_signup'),
    path('logout/', views.user_logout, name="user_logout"),
    path('generate_blog', views.generate_blog, name="generate_blog"),
    path('blog_list', views.blog_list, name="blog_list"),
    path('blog_details/<int:pk>', views.blog_details, name="blog_details"),
]
