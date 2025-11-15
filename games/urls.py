from django.urls import path
from . import views
from django.urls import path
from . import views
urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('<int:game_id>/', views.game_detail, name='game_detail'),
]

app_name = 'games'
urlpatterns = [
    path('', views.GameListView.as_view(), name='list'),
    path('top/', views.top_games, name='top'),
    path('export/', views.export_games_json, name='export_json'),
    path('import/', views.import_games_json, name='import_json'),
    path('add/', views.GameCreateView.as_view(), name='add'),
    path('<int:pk>/', views.GameDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.GameUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.GameDeleteView.as_view(), name='delete'),
]
