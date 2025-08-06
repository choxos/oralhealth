"""
Admin configuration for AI recommendations app.
"""

from django.contrib import admin
from .models import UserProfile, AIRecommendationSession, RecommendationMatch


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for user profiles."""
    
    list_display = [
        'session_id', 'age_group', 'location_country', 'caries_risk',
        'periodontal_status', 'created_at'
    ]
    list_filter = [
        'age_group', 'caries_risk', 'periodontal_status', 'fluoride_exposure',
        'has_orthodontics', 'has_diabetes', 'is_pregnant', 'created_at'
    ]
    search_fields = ['session_id', 'location_country', 'specific_concerns']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session_id', 'age_group', 'location_country')
        }),
        ('Oral Health Status', {
            'fields': ('caries_risk', 'periodontal_status', 'fluoride_exposure')
        }),
        ('Medical Conditions', {
            'fields': ('has_orthodontics', 'has_dental_implants', 'has_diabetes', 
                      'is_pregnant', 'has_dry_mouth')
        }),
        ('Behavioral Factors', {
            'fields': ('brushing_frequency', 'flossing_frequency', 'diet_sugar_intake')
        }),
        ('Additional Information', {
            'fields': ('specific_concerns', 'medications')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class RecommendationMatchInline(admin.TabularInline):
    """Inline for recommendation matches."""
    model = RecommendationMatch
    extra = 0
    readonly_fields = ['relevance_score', 'match_reasoning', 'priority_level']
    fields = ['recommendation', 'relevance_score', 'priority_level', 'match_reasoning']


@admin.register(AIRecommendationSession)
class AIRecommendationSessionAdmin(admin.ModelAdmin):
    """Admin for AI recommendation sessions."""
    
    list_display = [
        'user_profile', 'status', 'recommendations_count', 
        'processing_time', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['user_profile__session_id', 'error_message']
    readonly_fields = [
        'user_profile', 'processing_time', 'created_at', 'updated_at',
        'recommendations_count'
    ]
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user_profile', 'status', 'processing_time')
        }),
        ('AI Analysis', {
            'fields': ('gemini_analysis', 'personalized_advice', 'risk_assessment', 
                      'priority_actions')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    inlines = [RecommendationMatchInline]
    
    def recommendations_count(self, obj):
        return obj.recommendations_count
    recommendations_count.short_description = 'Recommendations'


@admin.register(RecommendationMatch)
class RecommendationMatchAdmin(admin.ModelAdmin):
    """Admin for recommendation matches."""
    
    list_display = [
        'ai_session', 'recommendation_title', 'relevance_score', 
        'priority_level', 'created_at'
    ]
    list_filter = ['priority_level', 'relevance_score', 'created_at']
    search_fields = ['recommendation__title', 'match_reasoning']
    readonly_fields = ['created_at']
    
    def recommendation_title(self, obj):
        return obj.recommendation.title[:50] + "..." if len(obj.recommendation.title) > 50 else obj.recommendation.title
    recommendation_title.short_description = 'Recommendation'