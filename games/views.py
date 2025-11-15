from django.shortcuts import render, get_object_or_404
from .models import Game
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Game
from .forms import GameForm

def game_list(request):
    games = Game.objects.all()
    return render(request, 'games/game_list.html', {'games': games})

def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    return render(request, 'games/game_detail.html', {'game': game})

# List + optional genre filter
class GameListView(ListView):
    model = Game
    template_name = 'games/game_list.html'
    context_object_name = 'games'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().order_by('-user_rating', '-release_year', 'title')
        genre = self.request.GET.get('genre')
        if genre:
            qs = qs.filter(genre__iexact=genre)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['genres'] = Game.objects.order_by('genre').values_list('genre', flat=True).distinct()
        ctx['selected_genre'] = self.request.GET.get('genre', '')
        return ctx

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'

class GameCreateView(CreateView):
    model = Game
    form_class = GameForm
    template_name = 'games/game_form.html'
    success_url = reverse_lazy('games:list')

class GameUpdateView(UpdateView):
    model = Game
    form_class = GameForm
    template_name = 'games/game_form.html'
    success_url = reverse_lazy('games:list')

class GameDeleteView(DeleteView):
    model = Game
    template_name = 'games/confirm_delete.html'
    success_url = reverse_lazy('games:list')

# Top N view (GET param n, default 10)
def top_games(request):
    try:
        n = int(request.GET.get('n', 10))
    except ValueError:
        n = 10
    n = max(1, min(n, 100))  # sanity check
    games = Game.objects.order_by('-user_rating', '-release_year')[:n]
    return render(request, 'games/top_games.html', {'games': games, 'n': n})

# Export JSON (download)
def export_games_json(request):
    qs = list(Game.objects.values('title', 'release_year', 'genre', 'user_rating'))
    data = json.dumps(qs, indent=2, ensure_ascii=False)
    filename = "games_export.json"
    response = HttpResponse(data, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# Import JSON (simple upload form + processing)
@require_http_methods(["GET", "POST"])
def import_games_json(request):
    message = None
    if request.method == "POST" and request.FILES.get('json_file'):
        f = request.FILES['json_file']
        try:
            raw = f.read().decode('utf-8')
            data = json.loads(raw)
            # Expecting a list of dicts with keys: title, release_year, genre, user_rating
            created = 0
            updated = 0
            errors = []
            for idx, item in enumerate(data):
                title = item.get('title')
                if not title:
                    errors.append(f'Entry {idx}: brak tytułu')
                    continue
                # fallback/defaults and types
                try:
                    year = int(item.get('release_year') or 0)
                except (TypeError, ValueError):
                    year = 0
                genre = item.get('genre') or ''
                try:
                    rating = int(item.get('user_rating') or 0)
                except (TypeError, ValueError):
                    rating = 0
                rating = max(0, min(rating, 10))
                obj, created_flag = Game.objects.update_or_create(
                    title=title,
                    defaults={'release_year': year, 'genre': genre, 'user_rating': rating}
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1
            message = f"Zaimportowano: {created} nowych, zaktualizowano: {updated}. Błędy: {len(errors)}"
        except Exception as e:
            message = f"Błąd podczas importu: {e}"
    return render(request, 'games/import_json.html', {'message': message})
