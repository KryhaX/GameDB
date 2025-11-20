from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_image_size(image):
    # ograniczenie do 2 MB
    max_mb = 2
    if image.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Plik obrazu nie może być większy niż {max_mb}MB.")


class Game(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.PositiveIntegerField()
    genre = models.CharField(max_length=100)
    user_rating = models.PositiveSmallIntegerField(default=0)  # 0–10
    cover = models.ImageField(upload_to='covers/', null=True, blank=True, validators=[validate_image_size])
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='games'
    )


    def __str__(self):
        return self.title


class Comment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField('Comment text')
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)  # optional: moderation

    class Meta:
        ordering = ['-created_at']  # newest first
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __str__(self):
        return f'Comment by {self.author} on {self.game}'
