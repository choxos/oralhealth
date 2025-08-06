"""
Views for AI-powered personalized recommendations.
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import FormView, DetailView
from .models import UserProfile, AIRecommendationSession, RecommendationMatch
from .forms import UserProfileForm
from .services import AIRecommendationService
import logging

logger = logging.getLogger(__name__)


class AIRecommendationFormView(FormView):
    """View for collecting user profile information."""
    
    template_name = 'ai_recommendations/profile_form.html'
    form_class = UserProfileForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'AI-Powered Oral Health Recommendations',
            'page_description': 'Get personalized oral health recommendations based on your profile and current evidence-based guidelines.',
        })
        return context
    
    def form_valid(self, form):
        """Process valid form and redirect to results."""
        try:
            # Save user profile
            user_profile = form.save()
            
            # Process recommendations in the background
            ai_service = AIRecommendationService()
            ai_session = ai_service.process_user_profile(user_profile)
            
            # Redirect to results page
            return redirect('ai_recommendations:results', session_id=user_profile.session_id)
            
        except Exception as e:
            logger.error(f"Error processing AI recommendations: {str(e)}")
            messages.error(
                self.request, 
                "We encountered an error processing your profile. Please try again or contact support if the problem persists."
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(
            self.request,
            "Please correct the errors below and try again."
        )
        return super().form_invalid(form)


class AIRecommendationResultsView(DetailView):
    """View for displaying AI recommendation results."""
    
    model = UserProfile
    template_name = 'ai_recommendations/results.html'
    context_object_name = 'user_profile'
    slug_field = 'session_id'
    slug_url_kwarg = 'session_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.object
        
        try:
            ai_session = user_profile.ai_session
            
            # Get recommendation matches ordered by relevance
            recommendation_matches = ai_session.matches.select_related(
                'recommendation__guideline__organization__country',
                'recommendation__strength',
                'recommendation__evidence_quality'
            ).prefetch_related(
                'recommendation__topics'
            ).order_by('-relevance_score')
            
            # Group matches by priority
            priority_groups = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            
            for match in recommendation_matches:
                priority_groups[match.priority_level].append(match)
            
            # Parse AI analysis sections
            ai_analysis = {}
            if ai_session.gemini_analysis:
                ai_analysis = self._parse_ai_sections(ai_session.gemini_analysis)
            
            context.update({
                'ai_session': ai_session,
                'recommendation_matches': recommendation_matches,
                'priority_groups': priority_groups,
                'ai_analysis': ai_analysis,
                'total_recommendations': recommendation_matches.count(),
                'page_title': 'Your Personalized Oral Health Recommendations',
                'page_description': f'AI-powered recommendations based on your oral health profile.',
            })
            
        except AIRecommendationSession.DoesNotExist:
            messages.error(
                self.request,
                "Your recommendation session could not be found. Please submit a new profile."
            )
            context['ai_session'] = None
        
        return context
    
    def _parse_ai_sections(self, analysis_text):
        """Parse AI analysis into sections for better display."""
        sections = {}
        current_section = None
        current_content = []
        
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if line.startswith('**') and line.endswith(':**'):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line.replace('**', '').replace(':', '').lower().replace(' ', '_')
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections


@require_http_methods(["GET"])
def ajax_session_status(request, session_id):
    """AJAX endpoint to check processing status."""
    try:
        user_profile = get_object_or_404(UserProfile, session_id=session_id)
        ai_session = user_profile.ai_session
        
        data = {
            'status': ai_session.status,
            'recommendations_count': ai_session.recommendations_count,
            'processing_time': ai_session.processing_time,
        }
        
        if ai_session.status == 'error':
            data['error_message'] = ai_session.error_message
        
        return JsonResponse(data)
        
    except (UserProfile.DoesNotExist, AIRecommendationSession.DoesNotExist):
        return JsonResponse({'status': 'not_found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def ajax_feedback(request):
    """AJAX endpoint for user feedback on recommendations."""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        recommendation_id = data.get('recommendation_id')
        helpful = data.get('helpful')
        
        # Log feedback for analysis
        logger.info(
            f"Recommendation feedback: session={session_id}, "
            f"recommendation={recommendation_id}, helpful={helpful}"
        )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        return JsonResponse({'status': 'error'}, status=400)


def about_ai_recommendations(request):
    """About page explaining the AI recommendations feature."""
    context = {
        'page_title': 'About AI Recommendations',
        'page_description': 'Learn how our AI-powered recommendations work and what makes them reliable.',
    }
    return render(request, 'ai_recommendations/about.html', context)