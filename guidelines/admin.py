"""
Optimized admin configuration for guidelines app.
"""

from django.contrib import admin
from .models import (
    Country, Organization, Guideline, Chapter, Topic, 
    RecommendationStrength, EvidenceQuality, Recommendation, RecommendationReference
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'website']
    list_filter = ['country']
    search_fields = ['name']
    ordering = ['name']


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ['number', 'title']


@admin.register(Guideline)
class GuidelineAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'publication_year', 'is_active']
    list_filter = ['organization__country', 'publication_year', 'is_active']
    search_fields = ['title', 'description']
    inlines = [ChapterInline]
    ordering = ['-publication_year', 'title']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['guideline', 'number', 'title']
    list_filter = ['guideline__organization__country']
    search_fields = ['title', 'content']
    ordering = ['guideline', 'number']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(RecommendationStrength)
class RecommendationStrengthAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'order']
    ordering = ['order', 'name']


@admin.register(EvidenceQuality)
class EvidenceQualityAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'order']
    ordering = ['order', 'name']


class RecommendationReferenceInline(admin.TabularInline):
    model = RecommendationReference
    extra = 0
    fields = ['text', 'url', 'pmid', 'doi']


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
    inlines = [RecommendationReferenceInline]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'text', 'guideline', 'chapter')
        }),
        ('Classification', {
            'fields': ('topics', 'strength', 'evidence_quality')
        }),
        ('Population & Context', {
            'fields': ('target_population', 'clinical_context')
        }),
        ('References & Links', {
            'fields': ('source_url', 'page_number')
        }),
        ('Search & Metadata', {
            'fields': ('keywords',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RecommendationReference)
class RecommendationReferenceAdmin(admin.ModelAdmin):
    list_display = ['recommendation', 'text_preview', 'pmid', 'doi']
    list_filter = ['recommendation__guideline__organization__country']
    search_fields = ['text', 'pmid', 'doi']
    ordering = ['recommendation', 'id']
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Reference Text'