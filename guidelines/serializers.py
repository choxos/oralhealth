"""
Serializers for the guidelines app API.
"""

from rest_framework import serializers
from .models import (
    Country, Organization, Guideline, Topic,
    RecommendationStrength, EvidenceQuality, 
    Recommendation, Reference
)


class CountrySerializer(serializers.ModelSerializer):
    recommendation_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Country
        fields = ['name', 'code', 'flag_emoji', 'recommendation_count']


class OrganizationSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    
    class Meta:
        model = Organization
        fields = ['name', 'country', 'website', 'description']


class TopicSerializer(serializers.ModelSerializer):
    recommendation_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Topic
        fields = ['name', 'slug', 'description', 'recommendation_count']


class RecommendationStrengthSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationStrength
        fields = ['name', 'code', 'description', 'color_class']


class EvidenceQualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceQuality
        fields = ['name', 'grade', 'description', 'color_class']


class ReferenceSerializer(serializers.ModelSerializer):
    citation = serializers.CharField(source='get_citation', read_only=True)
    
    class Meta:
        model = Reference
        fields = [
            'title', 'authors', 'journal', 'year', 'volume', 
            'pages', 'doi', 'pmid', 'url', 'reference_type', 'citation'
        ]


class GuidelineSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    recommendation_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Guideline
        fields = [
            'id', 'title', 'organization', 'publication_year', 
            'version', 'url', 'description', 'last_updated',
            'recommendation_count'
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    guideline = GuidelineSerializer(read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    strength = RecommendationStrengthSerializer(read_only=True)
    evidence_quality = EvidenceQualitySerializer(read_only=True)
    references = ReferenceSerializer(many=True, read_only=True)
    keywords_list = serializers.CharField(source='get_search_keywords', read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'title', 'text', 'guideline', 'topics',
            'strength', 'evidence_quality', 'target_population',
            'age_group', 'clinical_context', 'guideline_url',
            'page_number', 'keywords', 'keywords_list',
            'references', 'created_at', 'updated_at'
        ]