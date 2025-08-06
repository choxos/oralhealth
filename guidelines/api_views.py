"""
API views for the guidelines app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Recommendation, Guideline, Topic, Country
from .serializers import (
    RecommendationSerializer, GuidelineSerializer, 
    TopicSerializer, CountrySerializer
)


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for recommendations."""
    serializer_class = RecommendationSerializer
    
    def get_queryset(self):
        queryset = Recommendation.objects.select_related(
            'guideline__organization__country', 'strength', 'evidence_quality'
        ).prefetch_related('topics', 'references')
        
        # Filter by country
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(guideline__organization__country__code=country)
        
        # Filter by topic
        topic = self.request.query_params.get('topic')
        if topic:
            queryset = queryset.filter(topics__slug=topic)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(text__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        return queryset.distinct()


class GuidelineViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for guidelines."""
    serializer_class = GuidelineSerializer
    
    def get_queryset(self):
        return Guideline.objects.filter(is_active=True).select_related(
            'organization__country'
        ).prefetch_related('recommendations')


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for topics."""
    serializer_class = TopicSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Topic.objects.annotate(
            recommendation_count=Count('recommendations')
        )


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for countries."""
    serializer_class = CountrySerializer
    lookup_field = 'code'
    
    def get_queryset(self):
        return Country.objects.annotate(
            recommendation_count=Count('organization__guideline__recommendations')
        ).filter(recommendation_count__gt=0)


@api_view(['GET'])
def search_recommendations(request):
    """Search recommendations API endpoint."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return Response({'results': [], 'count': 0})
    
    recommendations = Recommendation.objects.filter(
        Q(title__icontains=query) |
        Q(text__icontains=query) |
        Q(keywords__icontains=query)
    ).select_related(
        'guideline__organization__country', 'strength', 'evidence_quality'
    )[:20]
    
    serializer = RecommendationSerializer(recommendations, many=True)
    return Response({
        'results': serializer.data,
        'count': len(serializer.data)
    })


@api_view(['GET'])
def get_statistics(request):
    """Get database statistics."""
    stats = {
        'total_recommendations': Recommendation.objects.count(),
        'total_guidelines': Guideline.objects.filter(is_active=True).count(),
        'total_countries': Country.objects.annotate(
            rec_count=Count('organization__guideline__recommendations')
        ).filter(rec_count__gt=0).count(),
        'total_topics': Topic.objects.count(),
        'by_country': {},
        'by_strength': {},
        'by_evidence_quality': {},
    }
    
    # Statistics by country
    country_stats = Country.objects.annotate(
        rec_count=Count('organization__guideline__recommendations')
    ).filter(rec_count__gt=0).values('name', 'code', 'rec_count')
    
    for country in country_stats:
        stats['by_country'][country['code']] = {
            'name': country['name'],
            'count': country['rec_count']
        }
    
    # Statistics by recommendation strength
    from .models import RecommendationStrength
    strength_stats = RecommendationStrength.objects.annotate(
        rec_count=Count('recommendation')
    ).values('name', 'code', 'rec_count')
    
    for strength in strength_stats:
        stats['by_strength'][strength['code']] = {
            'name': strength['name'],
            'count': strength['rec_count']
        }
    
    # Statistics by evidence quality
    from .models import EvidenceQuality
    quality_stats = EvidenceQuality.objects.annotate(
        rec_count=Count('recommendation')
    ).values('name', 'grade', 'rec_count')
    
    for quality in quality_stats:
        stats['by_evidence_quality'][quality['grade']] = {
            'name': quality['name'],
            'count': quality['rec_count']
        }
    
    return Response(stats)