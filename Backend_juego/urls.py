"""
URL configuration for Backend_juego project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path

from api import endpoints

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', endpoints.register_user),
    path('login/',endpoints.login),
    path('logout/',endpoints.logout_user),
    path('user/',endpoints.get_user),
    path('inventory/<int:character_id>/equip/', endpoints.favorite),
    path('characters/', endpoints.get_characters),
    path('shop/<int:character_id>/buy/',endpoints.comprar_personaje),
    path('run/save/',endpoints.post_runs),
    path('leaderboard/',endpoints.leaderboard),
    path('validar_token/',endpoints.validar_token),
]
