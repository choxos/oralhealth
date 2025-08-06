"""
Services for AI-powered personalized recommendations.
"""

import os
import json
import time
import logging
from typing import List, Dict, Tuple
from django.db.models import Q
from django.conf import settings
from guidelines.models import Recommendation, Country
from .models import UserProfile, AIRecommendationSession, RecommendationMatch

logger = logging.getLogger(__name__)


class RecommendationMatcher:
    """Service for matching user profiles to relevant recommendations."""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.recommendations = []
        self.scores = {}
    
    def find_matching_recommendations(self, limit: int = 20) -> List[Tuple[Recommendation, float]]:
        """Find and score recommendations based on user profile."""
        
        # Start with all recommendations
        queryset = Recommendation.objects.select_related(
            'guideline__organization__country',
            'strength',
            'evidence_quality'
        ).prefetch_related('topics')
        
        # Apply filters based on user profile
        queryset = self._apply_geographic_filter(queryset)
        queryset = self._apply_age_filter(queryset)
        queryset = self._apply_condition_filters(queryset)
        
        # Score each recommendation
        scored_recommendations = []
        for recommendation in queryset:
            score = self._calculate_relevance_score(recommendation)
            if score > 0.1:  # Only include recommendations with meaningful relevance
                scored_recommendations.append((recommendation, score))
        
        # Sort by score and return top matches
        scored_recommendations.sort(key=lambda x: x[1], reverse=True)
        return scored_recommendations[:limit]
    
    def _apply_geographic_filter(self, queryset):
        """Filter recommendations by geographic relevance."""
        country_name = self.user_profile.location_country.lower()
        
        # Try to match country to existing countries in database
        country_filters = Q()
        
        if 'united kingdom' in country_name or 'uk' in country_name:
            country_filters |= Q(guideline__organization__country__name__icontains='United Kingdom')
            country_filters |= Q(guideline__organization__country__name__icontains='England')
            country_filters |= Q(guideline__organization__country__name__icontains='Scotland')
        elif 'united states' in country_name or 'usa' in country_name or 'america' in country_name:
            country_filters |= Q(guideline__organization__country__name__icontains='United States')
        elif 'canada' in country_name:
            country_filters |= Q(guideline__organization__country__name__icontains='Canada')
        elif 'australia' in country_name:
            country_filters |= Q(guideline__organization__country__name__icontains='Australia')
        else:
            # If no specific match, include all countries but prefer international guidelines
            return queryset
        
        # Include international and WHO guidelines for all users
        country_filters |= Q(guideline__organization__name__icontains='WHO')
        country_filters |= Q(guideline__organization__name__icontains='International')
        
        return queryset.filter(country_filters)
    
    def _apply_age_filter(self, queryset):
        """Filter recommendations by age appropriateness."""
        age_group = self.user_profile.age_group
        
        # Age-related keywords in recommendations
        age_keywords = {
            '0-2': ['infant', 'baby', 'toddler', '0-2', 'under 2'],
            '3-5': ['preschool', 'child', 'children', '3-5', 'young child'],
            '6-12': ['school', 'child', 'children', '6-12', 'pediatric'],
            '13-17': ['adolescent', 'teenager', 'teen', '13-17', 'young adult'],
            '18-30': ['adult', 'young adult'],
            '31-50': ['adult'],
            '51-65': ['adult', 'middle-aged'],
            '65+': ['adult', 'elderly', 'senior', 'older adult', '65+'],
        }
        
        keywords = age_keywords.get(age_group, ['adult'])
        
        # Build filter for age-appropriate recommendations
        age_filter = Q()
        for keyword in keywords:
            age_filter |= Q(title__icontains=keyword)
            age_filter |= Q(text__icontains=keyword)
            age_filter |= Q(target_population__icontains=keyword)
        
        # Also include general recommendations that don't specify age
        general_filter = Q(target_population__isnull=True) | Q(target_population='')
        
        return queryset.filter(age_filter | general_filter)
    
    def _apply_condition_filters(self, queryset):
        """Filter recommendations based on specific conditions."""
        condition_filters = Q()
        
        # High caries risk
        if self.user_profile.caries_risk == 'high':
            condition_filters |= Q(title__icontains='caries')
            condition_filters |= Q(title__icontains='decay')
            condition_filters |= Q(title__icontains='fluoride')
            condition_filters |= Q(text__icontains='high risk')
        
        # Periodontal conditions
        if self.user_profile.periodontal_status in ['gingivitis', 'periodontitis']:
            condition_filters |= Q(title__icontains='periodontal')
            condition_filters |= Q(title__icontains='gum')
            condition_filters |= Q(title__icontains='gingivitis')
            condition_filters |= Q(title__icontains='periodontitis')
        
        # Orthodontics
        if self.user_profile.has_orthodontics:
            condition_filters |= Q(title__icontains='orthodontic')
            condition_filters |= Q(title__icontains='braces')
            condition_filters |= Q(text__icontains='orthodontic')
        
        # Diabetes
        if self.user_profile.has_diabetes:
            condition_filters |= Q(text__icontains='diabetes')
            condition_filters |= Q(text__icontains='diabetic')
        
        # Pregnancy
        if self.user_profile.is_pregnant:
            condition_filters |= Q(text__icontains='pregnancy')
            condition_filters |= Q(text__icontains='pregnant')
            condition_filters |= Q(target_population__icontains='pregnant')
        
        # Dry mouth
        if self.user_profile.has_dry_mouth:
            condition_filters |= Q(text__icontains='dry mouth')
            condition_filters |= Q(text__icontains='xerostomia')
        
        # If no specific conditions, return all
        if not condition_filters:
            return queryset
        
        # Include general oral health recommendations for all users
        general_filter = Q(title__icontains='oral health')
        general_filter |= Q(title__icontains='dental hygiene')
        general_filter |= Q(title__icontains='tooth brushing')
        
        return queryset.filter(condition_filters | general_filter)
    
    def _calculate_relevance_score(self, recommendation: Recommendation) -> float:
        """Calculate relevance score for a recommendation."""
        score = 0.0
        
        # Base score for all recommendations
        score += 0.1
        
        # Evidence quality bonus
        if recommendation.evidence_quality:
            quality_scores = {
                'High': 0.3,
                'Moderate': 0.2,
                'Low': 0.1,
                'Very Low': 0.05
            }
            quality_name = recommendation.evidence_quality.name
            for quality, bonus in quality_scores.items():
                if quality.lower() in quality_name.lower():
                    score += bonus
                    break
        
        # Strength of recommendation bonus
        if recommendation.strength:
            strength_scores = {
                'Strong': 0.25,
                'Conditional': 0.15,
                'Weak': 0.1
            }
            strength_name = recommendation.strength.name
            for strength, bonus in strength_scores.items():
                if strength.lower() in strength_name.lower():
                    score += bonus
                    break
        
        # Age appropriateness
        score += self._score_age_match(recommendation)
        
        # Condition-specific relevance
        score += self._score_condition_match(recommendation)
        
        # Geographic relevance
        score += self._score_geographic_match(recommendation)
        
        # Risk factor alignment
        score += self._score_risk_alignment(recommendation)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _score_age_match(self, recommendation: Recommendation) -> float:
        """Score based on age appropriateness."""
        age_group = self.user_profile.age_group
        text_lower = f"{recommendation.title} {recommendation.text}".lower()
        
        age_keywords = {
            '0-2': ['infant', 'baby', 'toddler'],
            '3-5': ['preschool', 'young child'],
            '6-12': ['school age', 'child', 'pediatric'],
            '13-17': ['adolescent', 'teenager', 'teen'],
            '18-30': ['young adult'],
            '31-50': ['adult'],
            '51-65': ['middle-aged', 'adult'],
            '65+': ['elderly', 'senior', 'older adult'],
        }
        
        keywords = age_keywords.get(age_group, [])
        for keyword in keywords:
            if keyword in text_lower:
                return 0.2
        
        # Penalty for age-inappropriate content
        all_age_keywords = [kw for kwds in age_keywords.values() for kw in kwds]
        other_keywords = [kw for kw in all_age_keywords if kw not in keywords]
        
        for keyword in other_keywords:
            if keyword in text_lower and keyword not in ['adult']:  # 'adult' is too general
                return -0.1
        
        return 0.0
    
    def _score_condition_match(self, recommendation: Recommendation) -> float:
        """Score based on specific conditions."""
        score = 0.0
        text_lower = f"{recommendation.title} {recommendation.text}".lower()
        
        # Caries risk
        if self.user_profile.caries_risk == 'high':
            if any(term in text_lower for term in ['high risk', 'caries', 'decay', 'fluoride']):
                score += 0.3
        
        # Periodontal status
        if self.user_profile.periodontal_status in ['gingivitis', 'periodontitis']:
            if any(term in text_lower for term in ['periodontal', 'gum', 'gingivitis']):
                score += 0.3
        
        # Special conditions
        conditions = [
            (self.user_profile.has_orthodontics, ['orthodontic', 'braces']),
            (self.user_profile.has_diabetes, ['diabetes', 'diabetic']),
            (self.user_profile.is_pregnant, ['pregnancy', 'pregnant']),
            (self.user_profile.has_dry_mouth, ['dry mouth', 'xerostomia']),
        ]
        
        for has_condition, keywords in conditions:
            if has_condition:
                if any(keyword in text_lower for keyword in keywords):
                    score += 0.25
        
        return score
    
    def _score_geographic_match(self, recommendation: Recommendation) -> float:
        """Score based on geographic relevance."""
        user_country = self.user_profile.location_country.lower()
        rec_country = recommendation.guideline.organization.country.name.lower()
        
        # Perfect match
        if user_country in rec_country or rec_country in user_country:
            return 0.3
        
        # Regional matches
        uk_countries = ['united kingdom', 'england', 'scotland', 'wales']
        if any(c in user_country for c in uk_countries) and any(c in rec_country for c in uk_countries):
            return 0.25
        
        # International guidelines are good for everyone
        org_name = recommendation.guideline.organization.name.lower()
        if any(term in org_name for term in ['who', 'international', 'world']):
            return 0.15
        
        return 0.0
    
    def _score_risk_alignment(self, recommendation: Recommendation) -> float:
        """Score based on risk factor alignment."""
        score = 0.0
        text_lower = f"{recommendation.title} {recommendation.text}".lower()
        
        # Fluoride recommendations based on exposure
        if 'fluoride' in text_lower:
            if self.user_profile.fluoride_exposure in ['none', 'water']:
                score += 0.2  # More relevant for low fluoride exposure
            elif self.user_profile.fluoride_exposure == 'professional':
                score += 0.1  # Already has professional care
        
        # Diet and sugar intake
        if self.user_profile.diet_sugar_intake == 'high':
            if any(term in text_lower for term in ['diet', 'sugar', 'frequency', 'snacking']):
                score += 0.2
        
        return score


class GeminiAIService:
    """Service for interacting with Google Gemini AI."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in settings")
    
    def analyze_recommendations(self, user_profile: UserProfile, recommendations: List[Recommendation]) -> Dict[str, str]:
        """Analyze recommendations using Gemini AI and provide personalized advice."""
        
        if not self.api_key:
            return self._generate_fallback_analysis(user_profile, recommendations)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = self._build_analysis_prompt(user_profile, recommendations)
            response = model.generate_content(prompt)
            
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            logger.error(f"Gemini AI analysis failed: {str(e)}")
            return self._generate_fallback_analysis(user_profile, recommendations)
    
    def _build_analysis_prompt(self, user_profile: UserProfile, recommendations: List[Recommendation]) -> str:
        """Build the prompt for Gemini AI analysis."""
        
        # User profile summary
        profile_summary = f"""
User Profile:
- Age: {user_profile.get_age_group_display()}
- Location: {user_profile.location_country}
- Caries Risk: {user_profile.get_caries_risk_display()}
- Gum Health: {user_profile.get_periodontal_status_display()}
- Fluoride Exposure: {user_profile.get_fluoride_exposure_display()}
- Special Conditions: {self._format_conditions(user_profile)}
- Oral Hygiene: Brushing {user_profile.brushing_frequency or 'not specified'}, Flossing {user_profile.flossing_frequency or 'not specified'}
- Diet: {user_profile.get_diet_sugar_intake_display() or 'not specified'}
- Specific Concerns: {user_profile.specific_concerns or 'None specified'}
- Medications: {user_profile.medications or 'None specified'}
"""
        
        # Recommendations summary
        rec_summaries = []
        for i, rec in enumerate(recommendations[:10], 1):  # Limit to top 10 for prompt length
            rec_summaries.append(f"""
{i}. {rec.title}
   Source: {rec.guideline.organization.name} ({rec.guideline.organization.country.name})
   Evidence: {rec.evidence_quality.name if rec.evidence_quality else 'Not specified'}
   Strength: {rec.strength.name if rec.strength else 'Not specified'}
   Content: {rec.text[:300]}...
""")
        
        recommendations_text = "\n".join(rec_summaries)
        
        prompt = f"""
You are an expert dental professional providing personalized oral health advice. Based on the user profile and evidence-based recommendations below, provide a comprehensive analysis.

{profile_summary}

Relevant Evidence-Based Recommendations:
{recommendations_text}

Please provide your analysis in the following structured format:

**RISK ASSESSMENT:**
Assess the user's overall oral health risk profile and identify key risk factors.

**PERSONALIZED ADVICE:**
Provide specific, actionable advice tailored to this user's profile, incorporating the evidence-based recommendations.

**PRIORITY ACTIONS:**
List 3-5 priority actions the user should take, ranked by importance.

**PREVENTIVE STRATEGIES:**
Suggest preventive measures specific to their risk factors and conditions.

**PROFESSIONAL CARE:**
Recommend when and what type of professional dental care they should seek.

**IMPORTANT NOTES:**
Include any important considerations, contraindications, or warnings relevant to their profile.

Keep your response practical, evidence-based, and easy to understand. Focus on actionable advice that aligns with the provided evidence-based recommendations.
"""
        
        return prompt
    
    def _format_conditions(self, profile: UserProfile) -> str:
        """Format special conditions for the prompt."""
        conditions = []
        if profile.has_orthodontics:
            conditions.append("Orthodontic treatment")
        if profile.has_dental_implants:
            conditions.append("Dental implants")
        if profile.has_diabetes:
            conditions.append("Diabetes")
        if profile.is_pregnant:
            conditions.append("Pregnancy")
        if profile.has_dry_mouth:
            conditions.append("Dry mouth")
        
        return ", ".join(conditions) if conditions else "None"
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, str]:
        """Parse the AI response into structured sections."""
        sections = {
            'risk_assessment': '',
            'personalized_advice': '',
            'priority_actions': '',
            'preventive_strategies': '',
            'professional_care': '',
            'important_notes': ''
        }
        
        current_section = None
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if '**RISK ASSESSMENT:**' in line:
                current_section = 'risk_assessment'
            elif '**PERSONALIZED ADVICE:**' in line:
                current_section = 'personalized_advice'
            elif '**PRIORITY ACTIONS:**' in line:
                current_section = 'priority_actions'
            elif '**PREVENTIVE STRATEGIES:**' in line:
                current_section = 'preventive_strategies'
            elif '**PROFESSIONAL CARE:**' in line:
                current_section = 'professional_care'
            elif '**IMPORTANT NOTES:**' in line:
                current_section = 'important_notes'
            elif current_section and line:
                sections[current_section] += line + '\n'
        
        # Combine all sections into a full analysis
        full_analysis = response_text
        
        return {
            'gemini_analysis': full_analysis,
            'risk_assessment': sections['risk_assessment'].strip(),
            'personalized_advice': sections['personalized_advice'].strip(),
            'priority_actions': sections['priority_actions'].strip(),
            'preventive_strategies': sections['preventive_strategies'].strip(),
            'professional_care': sections['professional_care'].strip(),
            'important_notes': sections['important_notes'].strip(),
        }
    
    def _generate_fallback_analysis(self, user_profile: UserProfile, recommendations: List[Recommendation]) -> Dict[str, str]:
        """Generate basic analysis when AI is not available."""
        
        # Basic risk assessment
        risk_factors = []
        if user_profile.caries_risk == 'high':
            risk_factors.append("high caries risk")
        if user_profile.periodontal_status in ['gingivitis', 'periodontitis']:
            risk_factors.append("gum disease")
        if user_profile.has_diabetes:
            risk_factors.append("diabetes")
        if user_profile.diet_sugar_intake == 'high':
            risk_factors.append("high sugar diet")
        
        risk_text = f"Based on your profile, you have {len(risk_factors)} identified risk factors: {', '.join(risk_factors)}." if risk_factors else "Your oral health risk appears to be low to moderate."
        
        # Basic advice
        advice_points = [
            "Follow evidence-based recommendations from reputable dental organizations",
            "Maintain regular oral hygiene practices",
            "Consider professional dental care based on your risk factors"
        ]
        
        if user_profile.caries_risk == 'high':
            advice_points.append("Focus on fluoride use and dietary modifications")
        
        if user_profile.periodontal_status != 'healthy':
            advice_points.append("Pay special attention to gum health and interdental cleaning")
        
        return {
            'gemini_analysis': f"Analysis based on {len(recommendations)} evidence-based recommendations.\n\n{risk_text}\n\nKey recommendations:\n" + "\n".join(f"• {point}" for point in advice_points),
            'risk_assessment': risk_text,
            'personalized_advice': "\n".join(f"• {point}" for point in advice_points),
            'priority_actions': "Review the evidence-based recommendations below and consult with a dental professional for personalized guidance.",
            'preventive_strategies': "Follow standard oral hygiene practices and address specific risk factors identified in your profile.",
            'professional_care': "Regular dental check-ups are recommended, with frequency based on your risk assessment.",
            'important_notes': "This analysis is based on general guidelines. Always consult with a qualified dental professional for personalized care."
        }


class AIRecommendationService:
    """Main service for coordinating AI recommendation process."""
    
    def __init__(self):
        self.matcher = None
        self.ai_service = GeminiAIService()
    
    def process_user_profile(self, user_profile: UserProfile) -> AIRecommendationSession:
        """Process user profile and generate AI recommendations."""
        
        start_time = time.time()
        
        # Create AI session
        ai_session = AIRecommendationSession.objects.create(
            user_profile=user_profile,
            status='processing'
        )
        
        try:
            # Find matching recommendations
            self.matcher = RecommendationMatcher(user_profile)
            scored_recommendations = self.matcher.find_matching_recommendations(limit=15)
            
            # Store recommendations and create matches
            recommendations = []
            for recommendation, score in scored_recommendations:
                recommendations.append(recommendation)
                ai_session.matched_recommendations.add(recommendation)
                
                # Determine priority level based on score
                if score >= 0.8:
                    priority = 'critical'
                elif score >= 0.6:
                    priority = 'high'
                elif score >= 0.4:
                    priority = 'medium'
                else:
                    priority = 'low'
                
                # Create detailed match record
                RecommendationMatch.objects.create(
                    ai_session=ai_session,
                    recommendation=recommendation,
                    relevance_score=score,
                    match_reasoning=self._generate_match_reasoning(user_profile, recommendation, score),
                    priority_level=priority
                )
            
            # Get AI analysis
            ai_analysis = self.ai_service.analyze_recommendations(user_profile, recommendations)
            
            # Update session with results
            ai_session.gemini_analysis = ai_analysis.get('gemini_analysis', '')
            ai_session.personalized_advice = ai_analysis.get('personalized_advice', '')
            ai_session.risk_assessment = ai_analysis.get('risk_assessment', '')
            
            # Extract priority actions
            priority_text = ai_analysis.get('priority_actions', '')
            priority_actions = [action.strip('• -') for action in priority_text.split('\n') if action.strip()]
            ai_session.priority_actions = priority_actions[:5]  # Limit to 5 actions
            
            ai_session.status = 'completed'
            ai_session.processing_time = time.time() - start_time
            ai_session.save()
            
            logger.info(f"Successfully processed AI recommendations for profile {user_profile.session_id}")
            
        except Exception as e:
            ai_session.status = 'error'
            ai_session.error_message = str(e)
            ai_session.processing_time = time.time() - start_time
            ai_session.save()
            
            logger.error(f"Failed to process AI recommendations for profile {user_profile.session_id}: {str(e)}")
            raise
        
        return ai_session
    
    def _generate_match_reasoning(self, user_profile: UserProfile, recommendation: Recommendation, score: float) -> str:
        """Generate explanation for why a recommendation matches the user profile."""
        
        reasons = []
        
        # Geographic relevance
        if user_profile.location_country.lower() in recommendation.guideline.organization.country.name.lower():
            reasons.append(f"Guideline from {recommendation.guideline.organization.country.name}")
        
        # Age appropriateness
        age_keywords = ['infant', 'child', 'adolescent', 'adult', 'senior']
        text_lower = f"{recommendation.title} {recommendation.text}".lower()
        for keyword in age_keywords:
            if keyword in text_lower:
                reasons.append(f"Age-appropriate ({keyword})")
                break
        
        # Condition matching
        if user_profile.caries_risk == 'high' and any(term in text_lower for term in ['caries', 'decay', 'fluoride']):
            reasons.append("Addresses high caries risk")
        
        if user_profile.periodontal_status != 'healthy' and any(term in text_lower for term in ['periodontal', 'gum']):
            reasons.append("Relevant to gum health concerns")
        
        # Evidence quality
        if recommendation.evidence_quality and 'high' in recommendation.evidence_quality.name.lower():
            reasons.append("High-quality evidence")
        
        # Default reasoning
        if not reasons:
            reasons.append("General oral health recommendation")
        
        return "; ".join(reasons) + f" (Relevance score: {score:.2f})"