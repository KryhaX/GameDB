from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.GameListView.as_view(), name='list'),
    path('top/', views.top_games, name='top'),
    path('export/', views.export_games_json, name='export_json'),
    path('import/', views.import_games_json, name='import_json'),
    path('add/', views.GameCreateView.as_view(), name='add'),

    # signup (registration)
    path('signup/', views.SignUpView.as_view(), name='signup'),

    path('<int:pk>/', views.GameDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.GameUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.GameDeleteView.as_view(), name='delete'),
]
