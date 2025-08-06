"""
Admin configuration for cochrane app.
"""

from django.contrib import admin
from .models import CochraneReview, CochraneSoFEntry


class CochraneSoFEntryInline(admin.TabularInline):
    model = CochraneSoFEntry
    extra = 0
    fields = ['outcome', 'measure', 'effect', 'certainty_of_evidence']


@admin.register(CochraneReview)
class CochraneReviewAdmin(admin.ModelAdmin):
    list_display = ['review_id', 'title', 'publication_date']
    search_fields = ['review_id', 'title', 'authors']
    list_filter = ['publication_date']
    inlines = [CochraneSoFEntryInline]
    ordering = ['-publication_date']


@admin.register(CochraneSoFEntry)
class CochraneSoFEntryAdmin(admin.ModelAdmin):
    list_display = ['review', 'outcome', 'measure', 'effect', 'certainty_of_evidence']
    list_filter = ['certainty_of_evidence', 'significant', 'review']
    search_fields = ['population', 'intervention', 'comparison', 'outcome']
    ordering = ['review', 'id']