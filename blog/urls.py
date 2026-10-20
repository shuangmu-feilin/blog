"""
URL configuration for blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from api import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # 博客列表、新建博客
    path('api/blog/', views.BlogView.as_view()),

    # 博客详细
    path('api/blog/<int:pk>/', views.BlogDetailView.as_view()),

    # 评论列表
    path('api/comment/<int:blog_id>/', views.CommentView.as_view()),

    # 注册
    path('api/register/', views.RegisterView.as_view()),

    # 登录
    path('api/login/', views.LoginView.as_view()),

    # 点赞
    path('api/favor/', views.FavorView.as_view()),

]
