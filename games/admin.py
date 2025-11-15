from django.contrib import admin
from django.utils.html import format_html
from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'genre', 'user_rating', 'cover_tag')
    list_filter = ('genre', 'release_year')

    def cover_tag(self, obj):
        if obj.cover:
            return format_html('<img src="{}" style="width:60px; height:auto;" />', obj.cover.url)
        return "-"
    cover_tag.short_description = 'Cover'
