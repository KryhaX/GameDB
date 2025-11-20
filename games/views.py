from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods

import json

from .models import Game, Comment
from .forms import GameForm, CommentForm


# -----------------------
# List / Detail Views
# -----------------------
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


# DetailView + FormMixin to display and post comments
class GameDetailView(FormMixin, DetailView):
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'
    form_class = CommentForm

    def get_success_url(self):
        # redirect back to the same game detail page after posting a comment
        return reverse('games:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # ensure form is available in context
        if 'form' not in ctx:
            ctx['form'] = self.get_form()
        # list visible comments for this game
        ctx['comments'] = self.object.comments.filter(is_visible=True).select_related('author')
        return ctx

    def post(self, request, *args, **kwargs):
        # populate self.object for FormMixin + DetailView behavior
        self.object = self.get_object()
        # require login to post a comment
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        # attach game and author, then save the comment
        comment = form.save(commit=False)
        comment.game = self.object
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)


# -----------------------
# Permissions mixin
# -----------------------
class OwnerOrStaffRequiredMixin(UserPassesTestMixin):
    """
    Allow access only if the request.user is the owner of the object or is staff/superuser.
    Used for UpdateView and DeleteView on Game.
    """
    def test_func(self):
        obj = self.get_object()
        if obj is None:
            return False
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        return (obj.owner == user) or user.is_staff or user.is_superuser

    def handle_no_permission(self):
        # raise 403 (can be customized to redirect or show message)
        raise PermissionDenied


# -----------------------
# Create / Update / Delete (Game)
# -----------------------
class GameCreateView(LoginRequiredMixin, CreateView):
    model = Game
    form_class = GameForm
    template_name = 'games/game_form.html'
    success_url = reverse_lazy('games:list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        # set owner to currently logged in user
        form.instance.owner = self.request.user
        return super().form_valid(form)


class GameUpdateView(LoginRequiredMixin, OwnerOrStaffRequiredMixin, UpdateView):
    model = Game
    form_class = GameForm
    template_name = 'games/game_form.html'
    success_url = reverse_lazy('games:list')
    login_url = reverse_lazy('login')


class GameDeleteView(LoginRequiredMixin, OwnerOrStaffRequiredMixin, DeleteView):
    model = Game
    template_name = 'games/confirm_delete.html'
    success_url = reverse_lazy('games:list')
    login_url = reverse_lazy('login')


# -----------------------
# Sign up view
# -----------------------
class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('games:list')

    def form_valid(self, form):
        user = form.save()                 # save and hash password
        login(self.request, user)          # auto login
        messages.success(self.request, f"Welcome, {user.username}! You are registered and logged in.")
        return super().form_valid(form)    # will redirect to success_url

    def form_invalid(self, form):
        # quick logging for runserver — remove in production
        print("SIGNUP FORM INVALID")
        print("POST DATA:", self.request.POST)
        print("FORM ERRORS:", form.errors.as_json())

        for field, errors in form.errors.items():
            for e in errors:
                messages.error(self.request, f"{field}: {e}")

        return super().form_invalid(form)


# -----------------------
# Top N view
# -----------------------
def top_games(request):
    try:
        n = int(request.GET.get('n', 10))
    except (ValueError, TypeError):
        n = 10
    n = max(1, min(n, 100))
    games = Game.objects.order_by('-user_rating', '-release_year')[:n]
    return render(request, 'games/top_games.html', {'games': games, 'n': n})


# -----------------------
# Export JSON (download)
# -----------------------
def export_games_json(request):
    qs = list(Game.objects.values('title', 'release_year', 'genre', 'user_rating', 'owner_id'))
    data = json.dumps(qs, indent=2, ensure_ascii=False)
    filename = "games_export.json"
    response = HttpResponse(data, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# -----------------------
# Import JSON (simple upload)
# -----------------------
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
                    errors.append(f'Entry {idx}: missing title')
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
            message = f"Imported: {created} new, updated: {updated}. Errors: {len(errors)}"
        except Exception as e:
            message = f"Error during import: {e}"
    return render(request, 'games/import_json.html', {'message': message})


# -----------------------
# Comment permission mixin + edit/delete views
# -----------------------
class CommentAuthorOrGameOwnerOrStaffMixin(UserPassesTestMixin):
    """
    Allow only the comment author, the game owner, or staff/superuser to edit/delete a comment.
    """
    def test_func(self):
        comment = self.get_object()
        user = getattr(self.request, "user", None)
        if comment is None or user is None or not user.is_authenticated:
            return False
        return (
            (comment.author == user) or
            (getattr(comment.game, 'owner', None) == user) or
            user.is_staff or
            user.is_superuser
        )

    def handle_no_permission(self):
        raise PermissionDenied


class CommentUpdateView(LoginRequiredMixin, CommentAuthorOrGameOwnerOrStaffMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'games/comment_form.html'

    def get_success_url(self):
        return reverse_lazy('games:detail', kwargs={'pk': self.object.game.pk})


class CommentDeleteView(LoginRequiredMixin, CommentAuthorOrGameOwnerOrStaffMixin, DeleteView):
    model = Comment
    template_name = 'games/comment_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('games:detail', kwargs={'pk': self.object.game.pk})
