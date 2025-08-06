"""
Admin configuration for guidelines app.
"""

from django.contrib import admin
from .models import (
    Country, Organization, Guideline, Chapter, Topic, 
    RecommendationStrength, EvidenceQuality, Recommendation, Reference
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'flag_emoji']
    search_fields = ['name', 'code']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'website']
    list_filter = ['country']
    search_fields = ['name', 'description']


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ['number', 'title', 'url']


@admin.register(Guideline)
class GuidelineAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'publication_year', 'is_active']
    list_filter = ['organization__country', 'publication_year', 'is_active']
    search_fields = ['title', 'description']
    inlines = [ChapterInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['guideline', 'number', 'title']
    list_filter = ['guideline__organization__country']
    search_fields = ['title', 'content']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(RecommendationStrength)
class RecommendationStrengthAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'color_class']


@admin.register(EvidenceQuality)
class EvidenceQualityAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'color_class']


class ReferenceInline(admin.TabularInline):
    model = Reference
    extra = 0
    fields = ['title', 'authors', 'journal', 'year', 'doi']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['title', 'guideline', 'strength', 'evidence_quality', 'created_at']
    list_filter = [
        'guideline__organization__country', 
        'strength', 
        'evidence_quality', 
        'topics',
        'created_at'
    ]
    search_fields = ['title', 'text', 'keywords']
    filter_horizontal = ['topics']
    inlines = [ReferenceInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'text', 'guideline', 'chapter')
        }),
        ('Classification', {
            'fields': ('topics', 'strength', 'evidence_quality')
        }),
        ('Population & Context', {
            'fields': ('target_population', 'age_group', 'clinical_context')
        }),
        ('References & Links', {
            'fields': ('guideline_url', 'page_number')
        }),
        ('Search & Metadata', {
            'fields': ('keywords',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'journal', 'year', 'recommendation']
    list_filter = ['year', 'journal', 'reference_type']
    search_fields = ['title', 'authors', 'doi', 'pmid']