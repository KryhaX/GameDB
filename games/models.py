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
    def __str__(self):
        return self.title
