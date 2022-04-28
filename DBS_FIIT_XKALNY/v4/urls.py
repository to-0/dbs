from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('players/<int:player_id>/game_exp/', views.v4_game_exp),
    path('players/<int:player_id>/game_objectives/', views.v4_game_objectives),
    path('players/<int:player_id>/abilities/', views.v4_abilities),
    path('test/', views.v4_tower_kills),
    path('patches/', views.v4_patches),
    path('matches/<int:match_id>/top_purchases/', views.v4_top_purchases),
    path('statistics/tower_kills/', views.v4_tower_kills),
    path('abilities/<int:ability_id>/usage/',views.v4_abilities_usage)

]
