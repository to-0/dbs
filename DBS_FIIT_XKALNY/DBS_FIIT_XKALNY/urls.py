"""DBS_FIIT_XKALNY URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, include

import v1.views
import v2.views
import v3.views
import v4

urlpatterns = [
    path('v1/health', v1.views.health),
    path('', v1.views.home),
    path('v2/patches/', v2.views.patches),
    path('v2/players/<int:player_id>/game_exp/', v2.views.game_exp),
    path('v2/players/<int:player_id>/game_objectives/', v2.views.game_objectives),
    path('v2/players/<int:player_id>/abilities/', v2.views.game_abilities),
    path('v3/matches/<int:match_id>/top_purchases/', v3.views.top_purchases),
    path('v3/abilities/<int:ability_id>/usage/', v3.views.abilities_usage),
    path('v3/statistics/tower_kills/', v3.views.tower_kills),
    path('v4/', include('v4.urls'))


]
