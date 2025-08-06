"""
Views for search app.
"""

from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from guidelines.models import Recommendation, Topic, Country


def search_results(request):
    """Search results page."""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Recommendation.objects.filter(
            Q(title__icontains=query) |
            Q(text__icontains=query) |
            Q(keywords__icontains=query)
        ).select_related('guideline__organization__country', 'strength', 'evidence_quality')[:50]
    
    context = {
        'query': query,
        'results': results,
        'page_title': f'Search Results for "{query}"' if query else 'Search',
    }
    return render(request, 'search/results.html', context)


def search_api(request):
    """API endpoint for search suggestions."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search in recommendation titles and keywords
    recommendations = Recommendation.objects.filter(
        Q(title__icontains=query) | Q(keywords__icontains=query)
    ).values('id', 'title', 'guideline__organization__country__name')[:10]
    
    results = [
        {
            'id': rec['id'],
            'title': rec['title'],
            'country': rec['guideline__organization__country__name'],
            'url': f"/recommendations/{rec['id']}/"
        }
        for rec in recommendations
    ]
    
    return JsonResponse({'results': results})