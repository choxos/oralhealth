"""
Views for the guidelines app.
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import (
    Country, Guideline, Recommendation, Topic, 
    RecommendationStrength, EvidenceQuality
)
from .forms import RecommendationSearchForm
from oralhealth.translation import translator


def home_view(request):
    """Home page view."""
    return home(request)

def home(request):
    """Home page with overview statistics and search."""
    # Get statistics
    stats = {
        'total_recommendations': Recommendation.objects.count(),
        'total_guidelines': Guideline.objects.filter(is_active=True).count(),
        'total_countries': Country.objects.count(),
        'total_topics': Topic.objects.count(),
    }
    
    # Get highest evidence quality recommendations from all countries
    from django.db.models import Case, When, IntegerField, Q
    import random
    
    # Define evidence quality ordering (highest to lowest)
    evidence_order = Case(
        When(evidence_quality__name='High', then=1),
        When(evidence_quality__name='Moderate', then=2),
        When(evidence_quality__name='Low', then=3),
        When(evidence_quality__name='Very Low', then=4),
        default=5,
        output_field=IntegerField()
    )
    
    # Define strength ordering (strongest to weakest)
    strength_order = Case(
        When(strength__name='Strong', then=1),
        When(strength__name='Moderate', then=2),
        When(strength__name='Weak', then=3),
        default=4,
        output_field=IntegerField()
    )
    
    # Get high-quality recommendations (High or Moderate evidence)
    high_quality_recs = Recommendation.objects.select_related(
        'guideline__organization__country', 'strength', 'evidence_quality'
    ).prefetch_related('topics').filter(
        Q(evidence_quality__name='High') | Q(evidence_quality__name='Moderate')
    ).annotate(
        evidence_priority=evidence_order,
        strength_priority=strength_order
    ).order_by('evidence_priority', 'strength_priority')
    
    # Get recommendations from each country separately to ensure diversity
    top_recommendations = []
    countries_with_recs = Country.objects.filter(
        organizations__guidelines__recommendations__evidence_quality__name__in=['High', 'Moderate']
    ).distinct()
    
    # Collect top recommendations from each country
    country_recs = {}
    for country in countries_with_recs:
        country_high_recs = high_quality_recs.filter(
            guideline__organization__country=country
        )[:5]  # Top 5 from each country
        if country_high_recs:
            country_recs[country.code] = list(country_high_recs)
    
    # Randomly select 10 recommendations ensuring country diversity
    if country_recs:
        # First, get at least one from each country if possible
        for country_code, recs in country_recs.items():
            if len(top_recommendations) < 10 and recs:
                selected_rec = random.choice(recs)
                top_recommendations.append(selected_rec)
                recs.remove(selected_rec)
        
        # Fill remaining slots randomly from all remaining high-quality recommendations
        all_remaining = []
        for recs in country_recs.values():
            all_remaining.extend(recs)
        
        while len(top_recommendations) < 10 and all_remaining:
            selected_rec = random.choice(all_remaining)
            top_recommendations.append(selected_rec)
            all_remaining.remove(selected_rec)
    
    # If we still don't have 10, fill with any remaining high-quality recommendations
    if len(top_recommendations) < 10:
        remaining_ids = [rec.id for rec in top_recommendations]
        additional_recs = high_quality_recs.exclude(id__in=remaining_ids)[:10-len(top_recommendations)]
        top_recommendations.extend(additional_recs)
    
    # Get featured countries with their guidelines
    countries_data = []
    countries = Country.objects.annotate(
        recommendation_count=Count('organizations__guidelines__recommendations')
    ).filter(recommendation_count__gt=0).order_by('-recommendation_count')[:4]
    
    # For each country, get the main guideline(s)
    for country in countries:
        # Get the guideline with the most recommendations for this country
        main_guideline = Guideline.objects.filter(
            organization__country=country
        ).annotate(
            rec_count=Count('recommendations')
        ).order_by('-rec_count').first()
        
        country_info = {
            'country': country,
            'recommendation_count': country.recommendation_count,
            'main_guideline': main_guideline,
        }
        countries_data.append(country_info)
    
    # Search form
    search_form = RecommendationSearchForm()
    
    context = {
        'stats': stats,
        'top_recommendations': top_recommendations,
        'countries': countries_data,
        'search_form': search_form,
        'page_title': 'Oral Health Recommendations - Evidence-Based Clinical Guidelines',
        'page_description': 'Comprehensive database of oral health recommendations from UK, Scotland, and international guidelines.',
        'supported_languages': translator.get_supported_languages(),
    }
    
    return render(request, 'guidelines/home.html', context)


class RecommendationListView(ListView):
    """List view for recommendations with search and filtering."""
    model = Recommendation
    template_name = 'guidelines/recommendation_list.html'
    context_object_name = 'recommendations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Recommendation.objects.select_related(
            'guideline__organization__country'
        ).prefetch_related('topics')
        
        # Apply search filters
        form = RecommendationSearchForm(self.request.GET)
        if form.is_valid():
            search_query = form.cleaned_data.get('search')
            country = form.cleaned_data.get('country')
            topic = form.cleaned_data.get('topic')
            strength = form.cleaned_data.get('strength')
            evidence_quality = form.cleaned_data.get('evidence_quality')
            
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(text__icontains=search_query) |
                    Q(keywords__icontains=search_query)
                )
            
            if country:
                queryset = queryset.filter(guideline__organization__country=country)
            
            if topic:
                queryset = queryset.filter(topics=topic)
            
            if strength:
                queryset = queryset.filter(strength=strength)
            
            if evidence_quality:
                queryset = queryset.filter(evidence_quality=evidence_quality)
        
        return queryset.distinct().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RecommendationSearchForm(self.request.GET)
        context['page_title'] = 'Oral Health Recommendations'
        context['supported_languages'] = translator.get_supported_languages()
        return context


class RecommendationDetailView(DetailView):
    """Detail view for individual recommendations."""
    model = Recommendation
    template_name = 'guidelines/recommendation_detail.html'
    context_object_name = 'recommendation'
    
    def get_queryset(self):
        return Recommendation.objects.select_related(
            'guideline__organization__country', 'chapter'
        ).prefetch_related('topics', 'references')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recommendation = self.object
        
        # Get requested language
        target_lang = self.request.GET.get('lang', 'en')
        
        # Translate recommendation if needed
        if target_lang != 'en':
            translated = translator.translate_recommendation(recommendation, target_lang)
            context['translated_recommendation'] = translated
            context['current_language'] = target_lang
        
        # Get related recommendations
        related_recommendations = Recommendation.objects.filter(
            topics__in=recommendation.topics.all()
        ).exclude(pk=recommendation.pk).distinct()[:5]
        
        context['related_recommendations'] = related_recommendations
        context['page_title'] = recommendation.title
        context['supported_languages'] = translator.get_supported_languages()
        context['current_language'] = target_lang
        return context


class GuidelineListView(ListView):
    """List view for guidelines."""
    model = Guideline
    template_name = 'guidelines/guideline_list.html'
    context_object_name = 'guidelines'
    
    def get_queryset(self):
        return Guideline.objects.filter(is_active=True).select_related(
            'organization__country'
        ).annotate(
            recommendation_count=Count('recommendations')
        ).order_by('-publication_year')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Oral Health Guidelines'
        context['supported_languages'] = translator.get_supported_languages()
        return context


class GuidelineDetailView(DetailView):
    """Detail view for individual guidelines."""
    model = Guideline
    template_name = 'guidelines/guideline_detail.html'
    context_object_name = 'guideline'
    
    def get_queryset(self):
        return Guideline.objects.filter(is_active=True).select_related(
            'organization__country'
        ).prefetch_related(
            'chapters'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        guideline = self.object
        
        # Get recommendations by chapter
        recommendations_by_chapter = {}
        for recommendation in guideline.recommendations.all():
            chapter = recommendation.chapter
            if chapter:
                if chapter not in recommendations_by_chapter:
                    recommendations_by_chapter[chapter] = []
                recommendations_by_chapter[chapter].append(recommendation)
        
        context['recommendations_by_chapter'] = recommendations_by_chapter
        context['page_title'] = guideline.title
        context['supported_languages'] = translator.get_supported_languages()
        return context


class TopicListView(ListView):
    """List view for topics."""
    model = Topic
    template_name = 'guidelines/topic_list.html'
    context_object_name = 'topics'
    
    def get_queryset(self):
        return Topic.objects.filter(parent=None).annotate(
            recommendation_count=Count('recommendations')
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Oral Health Topics'
        context['supported_languages'] = translator.get_supported_languages()
        return context


class TopicDetailView(DetailView):
    """Detail view for individual topics."""
    model = Topic
    template_name = 'guidelines/topic_detail.html'
    context_object_name = 'topic'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.object
        
        # Get requested language
        target_lang = self.request.GET.get('lang', 'en')
        
        # Translate topic if needed
        if target_lang != 'en':
            translated = translator.translate_topic(topic, target_lang)
            context['translated_topic'] = translated
        
        # Get recommendations for this topic
        recommendations = Recommendation.objects.filter(
            topics=topic
        ).select_related(
            'guideline__organization__country'
        ).order_by('-created_at')
        
        # Paginate recommendations
        paginator = Paginator(recommendations, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['recommendations'] = page_obj
        context['page_title'] = f'Topic: {topic.name}'
        context['supported_languages'] = translator.get_supported_languages()
        context['current_language'] = target_lang
        return context


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


@cache_page(60 * 15)  # Cache for 15 minutes
def translate_api(request):
    """API endpoint for translating text."""
    text = request.GET.get('text', '').strip()
    target_lang = request.GET.get('target', 'en')
    source_lang = request.GET.get('source', 'en')
    
    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)
    
    if target_lang not in translator.SUPPORTED_LANGUAGES:
        return JsonResponse({'error': 'Unsupported target language'}, status=400)
    
    try:
        translated_text = translator.translate_text(text, target_lang, source_lang)
        return JsonResponse({
            'original': text,
            'translated': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'language_name': translator.SUPPORTED_LANGUAGES[target_lang]['name']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)