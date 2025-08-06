"""
API views for OralHealth app.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.db.models import Q, Count, Prefetch
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views import View

from guidelines.models import (
    Recommendation, Guideline, Country, Topic, 
    RecommendationStrength, EvidenceQuality
)
from cochrane.models import CochraneReview, CochraneSoFEntry


class APIDocsView(View):
    """API documentation page."""
    
    def get(self, request):
        context = {
            'page_title': 'OralHealth API Documentation',
            'page_description': 'RESTful API for accessing oral health recommendations and evidence.',
        }
        return render(request, 'api/docs.html', context)


@cache_page(60 * 15)  # Cache for 15 minutes
@require_http_methods(["GET"])
def recommendations_api(request):
    """
    API endpoint for recommendations.
    
    Query parameters:
    - q: Search query
    - country: Country code
    - topic: Topic ID
    - strength: Strength ID
    - evidence_quality: Evidence quality ID
    - page: Page number (default: 1)
    - limit: Results per page (default: 20, max: 100)
    """
    
    # Get query parameters
    query = request.GET.get('q', '')
    country_code = request.GET.get('country', '')
    topic_id = request.GET.get('topic', '')
    strength_id = request.GET.get('strength', '')
    evidence_quality_id = request.GET.get('evidence_quality', '')
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    # Base queryset
    queryset = Recommendation.objects.select_related(
        'guideline__organization__country',
        'strength',
        'evidence_quality'
    ).prefetch_related('topics')
    
    # Apply filters
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(text__icontains=query) |
            Q(keywords__icontains=query)
        )
    
    if country_code:
        queryset = queryset.filter(guideline__organization__country__code=country_code)
    
    if topic_id:
        try:
            queryset = queryset.filter(topics=int(topic_id))
        except (ValueError, TypeError):
            pass
    
    if strength_id:
        try:
            queryset = queryset.filter(strength=int(strength_id))
        except (ValueError, TypeError):
            pass
    
    if evidence_quality_id:
        try:
            queryset = queryset.filter(evidence_quality=int(evidence_quality_id))
        except (ValueError, TypeError):
            pass
    
    # Pagination
    paginator = Paginator(queryset, limit)
    recommendations_page = paginator.get_page(page)
    
    # Serialize data
    recommendations_data = []
    for rec in recommendations_page:
        rec_data = {
            'id': rec.id,
            'title': rec.title,
            'text': rec.text,
            'keywords': rec.keywords,
            'target_population': rec.target_population,
            'clinical_context': rec.clinical_context,
            'source_url': rec.source_url,
            'page_number': rec.page_number,
            'created_at': rec.created_at.isoformat(),
            'guideline': {
                'id': rec.guideline.id,
                'title': rec.guideline.title,
                'organization': rec.guideline.organization.name,
                'country': {
                    'name': rec.guideline.organization.country.name,
                    'code': rec.guideline.organization.country.code,
                    'flag_emoji': rec.guideline.organization.country.flag_emoji,
                    'display_name': f"{rec.guideline.organization.country.flag_emoji} {rec.guideline.organization.country.name}",
                },
                'publication_year': rec.guideline.publication_year,
                'url': rec.guideline.url,
            },
            'topics': [
                {'id': topic.id, 'name': topic.name, 'slug': topic.slug}
                for topic in rec.topics.all()
            ],
            'strength': {
                'id': rec.strength.id,
                'name': rec.strength.name,
                'description': rec.strength.description,
            } if rec.strength else None,
            'evidence_quality': {
                'id': rec.evidence_quality.id,
                'name': rec.evidence_quality.name,
                'description': rec.evidence_quality.description,
            } if rec.evidence_quality else None,
        }
        recommendations_data.append(rec_data)
    
    # Response data
    response_data = {
        'success': True,
        'data': recommendations_data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'total_results': paginator.count,
            'has_next': recommendations_page.has_next(),
            'has_previous': recommendations_page.has_previous(),
        },
        'filters_applied': {
            'query': query,
            'country': country_code,
            'topic': topic_id,
            'strength': strength_id,
            'evidence_quality': evidence_quality_id,
        }
    }
    
    return JsonResponse(response_data)


@cache_page(60 * 15)
@require_http_methods(["GET"])
def guidelines_api(request):
    """
    API endpoint for guidelines.
    
    Query parameters:
    - q: Search query
    - country: Country code
    - page: Page number (default: 1)
    - limit: Results per page (default: 20, max: 100)
    """
    
    # Get query parameters
    query = request.GET.get('q', '')
    country_code = request.GET.get('country', '')
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    # Base queryset
    queryset = Guideline.objects.select_related(
        'organization__country'
    ).annotate(
        recommendation_count=Count('recommendations')
    ).filter(is_active=True)
    
    # Apply filters
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(organization__name__icontains=query)
        )
    
    if country_code:
        queryset = queryset.filter(organization__country__code=country_code)
    
    # Pagination
    paginator = Paginator(queryset, limit)
    guidelines_page = paginator.get_page(page)
    
    # Serialize data
    guidelines_data = []
    for guideline in guidelines_page:
        guideline_data = {
            'id': guideline.id,
            'title': guideline.title,
            'description': guideline.description,
            'organization': {
                'id': guideline.organization.id,
                'name': guideline.organization.name,
                'website': guideline.organization.website,
                'country': {
                    'name': guideline.organization.country.name,
                    'code': guideline.organization.country.code,
                    'flag_emoji': guideline.organization.country.flag_emoji,
                    'display_name': f"{guideline.organization.country.flag_emoji} {guideline.organization.country.name}",
                }
            },
            'publication_year': guideline.publication_year,
            'url': guideline.url,
            'is_active': guideline.is_active,
            'recommendation_count': guideline.recommendation_count,
            'created_at': guideline.created_at.isoformat(),
        }
        guidelines_data.append(guideline_data)
    
    # Response data
    response_data = {
        'success': True,
        'data': guidelines_data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'total_results': paginator.count,
            'has_next': guidelines_page.has_next(),
            'has_previous': guidelines_page.has_previous(),
        },
        'filters_applied': {
            'query': query,
            'country': country_code,
        }
    }
    
    return JsonResponse(response_data)


@cache_page(60 * 15)
@require_http_methods(["GET"])
def cochrane_reviews_api(request):
    """
    API endpoint for Cochrane reviews.
    
    Query parameters:
    - q: Search query
    - page: Page number (default: 1)
    - limit: Results per page (default: 20, max: 100)
    """
    
    # Get query parameters
    query = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    # Base queryset
    queryset = CochraneReview.objects.annotate(
        sof_count=Count('sof_entries')
    )
    
    # Apply filters
    if query:
        queryset = queryset.filter(
            Q(review_id__icontains=query) |
            Q(filename__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(queryset, limit)
    reviews_page = paginator.get_page(page)
    
    # Serialize data
    reviews_data = []
    for review in reviews_page:
        review_data = {
            'id': review.id,
            'review_id': review.review_id,
            'filename': review.filename,
            'sof_count': review.sof_count,
            'created_at': review.created_at.isoformat(),
        }
        reviews_data.append(review_data)
    
    # Response data
    response_data = {
        'success': True,
        'data': reviews_data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'total_results': paginator.count,
            'has_next': reviews_page.has_next(),
            'has_previous': reviews_page.has_previous(),
        },
        'filters_applied': {
            'query': query,
        }
    }
    
    return JsonResponse(response_data)


@cache_page(60 * 30)
@require_http_methods(["GET"])
def stats_api(request):
    """
    API endpoint for statistics.
    """
    
    stats = {
        'recommendations': {
            'total': Recommendation.objects.count(),
            'by_country': [
                {
                    'name': country.name,
                    'code': country.code,
                    'flag_emoji': country.flag_emoji,
                    'display_name': f"{country.flag_emoji} {country.name}",
                    'count': country.count,
                }
                for country in Country.objects.annotate(
                    count=Count('organizations__guidelines__recommendations')
                ).filter(count__gt=0)
            ],
            'by_topic': list(
                Topic.objects.annotate(
                    count=Count('recommendations')
                ).filter(count__gt=0).values('name', 'slug', 'count')[:10]
            ),
        },
        'guidelines': {
            'total': Guideline.objects.filter(is_active=True).count(),
            'by_country': [
                {
                    'name': country.name,
                    'code': country.code,
                    'flag_emoji': country.flag_emoji,
                    'display_name': f"{country.flag_emoji} {country.name}",
                    'count': country.count,
                }
                for country in Country.objects.annotate(
                    count=Count('organizations__guidelines', filter=Q(organizations__guidelines__is_active=True))
                ).filter(count__gt=0)
            ],
        },
        'cochrane': {
            'total_reviews': CochraneReview.objects.count(),
            'total_sof_entries': CochraneSoFEntry.objects.count(),
        }
    }
    
    return JsonResponse({
        'success': True,
        'data': stats
    })


@require_http_methods(["GET"])
def metadata_api(request):
    """
    API endpoint for metadata (countries, topics, strengths, etc.).
    """
    
    metadata = {
        'countries': [
            {
                'id': country.id,
                'name': country.name,
                'code': country.code,
                'flag_emoji': country.flag_emoji,
                'display_name': f"{country.flag_emoji} {country.name}",
            }
            for country in Country.objects.all()
        ],
        'topics': list(
            Topic.objects.values('id', 'name', 'slug', 'description')
        ),
        'recommendation_strengths': list(
            RecommendationStrength.objects.values('id', 'name', 'description')
        ),
        'evidence_qualities': list(
            EvidenceQuality.objects.values('id', 'name', 'description')
        ),
    }
    
    return JsonResponse({
        'success': True,
        'data': metadata
    })