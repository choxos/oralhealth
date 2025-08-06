"""
Views for cochrane app.
"""

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import CochraneReview, CochraneSoFEntry


def cochrane_review_list(request):
    """List all Cochrane reviews."""
    reviews = CochraneReview.objects.all().order_by('-publication_date')
    
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reviews': page_obj,
        'page_title': 'Cochrane Oral Health Reviews',
    }
    return render(request, 'cochrane/review_list.html', context)


def cochrane_review_detail(request, review_id):
    """Detail view for a Cochrane review."""
    review = get_object_or_404(CochraneReview, review_id=review_id)
    sof_entries = review.sof_entries.all()
    
    context = {
        'review': review,
        'sof_entries': sof_entries,
        'page_title': review.title,
    }
    return render(request, 'cochrane/review_detail.html', context)