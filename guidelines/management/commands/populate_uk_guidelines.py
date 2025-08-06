"""
Management command to populate UK oral health guidelines.
Fetches data directly from gov.uk or uses local files.
"""

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from guidelines.models import (
    Country, Organization, Guideline, Chapter, Topic,
    RecommendationStrength, EvidenceQuality, Recommendation, RecommendationReference
)
import os
import re
from datetime import date


class Command(BaseCommand):
    help = 'Populate database with UK oral health guidelines'

    # UK Guidelines chapters
    GUIDELINE_CHAPTERS = {
        1: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-1-introduction",
        2: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-2-summary-guidance-tables-for-dental-teams",
        3: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-3-behaviour-change",
        4: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-4-dental-caries",
        5: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-5-periodontal-diseases",
        6: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-6-oral-cancer",
        7: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-7-tooth-wear",
        8: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-8-oral-hygiene",
        9: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-9-fluoride",
        10: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-10-healthier-eating",
        11: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-11-smoking-and-tobacco-use",
        12: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-12-alcohol",
        13: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-13-evidence-base-for-recommendations-in-the-summary-guidance-tables",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--offline',
            action='store_true',
            help='Use local files instead of fetching from web',
        )
        parser.add_argument(
            '--chapters',
            type=str,
            help='Comma-separated list of chapter numbers to process (e.g., "1,2,3")',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting UK guidelines population...'))
        
        with transaction.atomic():
            self.setup_base_data()
            
            # Determine which chapters to process
            if options['chapters']:
                chapter_nums = [int(x.strip()) for x in options['chapters'].split(',')]
            else:
                chapter_nums = list(self.GUIDELINE_CHAPTERS.keys())
            
            for chapter_num in chapter_nums:
                if chapter_num in self.GUIDELINE_CHAPTERS:
                    self.process_chapter(chapter_num, options['offline'])
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Chapter {chapter_num} not found')
                    )
        
        self.stdout.write(self.style.SUCCESS('Finished populating UK guidelines!'))

    def setup_base_data(self):
        """Setup countries, organizations, and classification systems."""
        
        # Create country
        uk, created = Country.objects.get_or_create(
            code='UK',
            defaults={'name': 'United Kingdom'}
        )
        if created:
            self.stdout.write(f'Created country: {uk.name}')
        
        # Create organization
        ohid, created = Organization.objects.get_or_create(
            name='Office for Health Improvement & Disparities',
            country=uk,
            defaults={
                'website': 'https://www.gov.uk/government/organisations/office-for-health-improvement-and-disparities'
            }
        )
        if created:
            self.stdout.write(f'Created organization: {ohid.name}')
        
        # Create guideline
        self.guideline, created = Guideline.objects.get_or_create(
            title='Delivering better oral health: an evidence-based toolkit for prevention',
            organization=ohid,
            defaults={
                'publication_year': 2021,
                'last_updated': date(2021, 11, 9),
                'url': 'https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention',
                'description': 'An evidence-based toolkit to support dental teams in improving their patient\'s oral and general health.',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created guideline: {self.guideline.title}')
        
        # Create recommendation strengths
        strengths = [
            ('Strong', 'Evidence-based strong recommendation', 1),
            ('Moderate', 'Evidence-based moderate recommendation', 2),
            ('Weak', 'Evidence-based weak recommendation', 3),
            ('Good Practice Point', 'Good practice recommendation', 4),
        ]
        
        for name, desc, order in strengths:
            strength, created = RecommendationStrength.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'order': order}
            )
            if created:
                self.stdout.write(f'Created strength: {name}')
        
        # Create evidence quality levels
        qualities = [
            ('High', 'High certainty evidence (GRADE)', 1),
            ('Moderate', 'Moderate certainty evidence (GRADE)', 2),
            ('Low', 'Low certainty evidence (GRADE)', 3),
            ('Very Low', 'Very low certainty evidence (GRADE)', 4),
        ]
        
        for name, desc, order in qualities:
            quality, created = EvidenceQuality.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'order': order}
            )
            if created:
                self.stdout.write(f'Created evidence quality: {name}')

    def process_chapter(self, chapter_num, offline=False):
        """Process a single chapter."""
        self.stdout.write(f'Processing Chapter {chapter_num}...')
        
        if offline:
            content = self.load_local_chapter(chapter_num)
        else:
            content = self.fetch_chapter_content(chapter_num)
        
        if not content:
            self.stdout.write(
                self.style.WARNING(f'No content found for Chapter {chapter_num}')
            )
            return
        
        # Create chapter
        chapter, created = Chapter.objects.get_or_create(
            guideline=self.guideline,
            number=chapter_num,
            defaults={
                'title': content['title'],
                'content': content['text'][:5000]  # Truncate for demo
            }
        )
        if created:
            self.stdout.write(f'Created chapter: {chapter.title}')
        
        # Extract and create recommendations
        recommendations = self.extract_recommendations(content['text'], chapter)
        for rec_data in recommendations:
            self.create_recommendation(rec_data, chapter)

    def load_local_chapter(self, chapter_num):
        """Load chapter from local file."""
        file_path = f'guidelines/uk_chapters/chapter_{chapter_num:02d}_*.md'
        # In a real implementation, you'd use glob to find the file
        # For now, return None to trigger web fetch
        return None

    def fetch_chapter_content(self, chapter_num):
        """Fetch chapter content from gov.uk website."""
        url = self.GUIDELINE_CHAPTERS[chapter_num]
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', class_='gem-c-title__text')
            title = title_elem.text.strip() if title_elem else f'Chapter {chapter_num}'
            
            # Extract main content
            content_div = soup.find('div', class_='govuk-govspeak')
            if content_div:
                # Clean up and extract text
                text_content = self.clean_html_content(content_div)
                
                return {
                    'title': title,
                    'text': text_content,
                    'url': url
                }
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to fetch Chapter {chapter_num}: {e}')
            )
        
        return None

    def clean_html_content(self, content_div):
        """Extract and clean text content from HTML."""
        # Remove unwanted elements
        for unwanted in content_div.find_all(['script', 'style', 'nav']):
            unwanted.decompose()
        
        # Extract text with basic formatting
        text_parts = []
        for elem in content_div.find_all(['h2', 'h3', 'h4', 'p', 'li']):
            text = elem.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short text
                if elem.name in ['h2', 'h3', 'h4']:
                    text_parts.append(f'\n## {text}\n')
                else:
                    text_parts.append(text)
        
        return '\n\n'.join(text_parts)

    def extract_recommendations(self, text, chapter):
        """Extract recommendations from chapter text."""
        recommendations = []
        
        # Simple pattern matching for demonstration
        # In a real implementation, you'd use more sophisticated NLP
        
        # Look for recommendation patterns
        rec_patterns = [
            r'should\s+(?:be\s+)?(?:advised|recommended|encouraged)',
            r'it\s+is\s+recommended',
            r'dental\s+teams\s+should',
            r'practitioners\s+should',
        ]
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            for pattern in rec_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    # Extract topic from sentence
                    topic_name = self.extract_topic_from_sentence(sentence)
                    
                    recommendations.append({
                        'title': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        'text': sentence,
                        'topic': topic_name,
                        'strength': 'Moderate',  # Default
                        'evidence_quality': 'Moderate'  # Default
                    })
                    break
        
        return recommendations[:5]  # Limit for demo

    def extract_topic_from_sentence(self, sentence):
        """Extract topic from recommendation sentence."""
        # Simple keyword-based topic extraction
        topics = {
            'fluoride': ['fluoride', 'fluorine'],
            'oral hygiene': ['brush', 'toothbrush', 'clean', 'hygiene'],
            'diet': ['sugar', 'diet', 'food', 'drink', 'eating'],
            'tobacco': ['smok', 'tobacco', 'cigarette'],
            'alcohol': ['alcohol', 'drink'],
            'dental caries': ['caries', 'decay', 'cavit'],
            'periodontal': ['gum', 'periodontal', 'gingivitis'],
        }
        
        sentence_lower = sentence.lower()
        
        for topic, keywords in topics.items():
            if any(keyword in sentence_lower for keyword in keywords):
                return topic
        
        return 'general'

    def create_recommendation(self, rec_data, chapter):
        """Create a recommendation in the database."""
        
        # Get or create topic
        topic, created = Topic.objects.get_or_create(
            name=rec_data['topic'].title(),
            defaults={'description': f'Recommendations related to {rec_data["topic"]}'}
        )
        if created:
            self.stdout.write(f'Created topic: {topic.name}')
        
        # Get strength and evidence quality
        try:
            strength = RecommendationStrength.objects.get(name=rec_data['strength'])
            evidence_quality = EvidenceQuality.objects.get(name=rec_data['evidence_quality'])
        except:
            strength = RecommendationStrength.objects.first()
            evidence_quality = EvidenceQuality.objects.first()
        
        # Create recommendation
        recommendation, created = Recommendation.objects.get_or_create(
            title=rec_data['title'],
            guideline=self.guideline,
            defaults={
                'text': rec_data['text'],
                'chapter': chapter,
                'strength': strength,
                'evidence_quality': evidence_quality,
                'keywords': rec_data['topic'],
                'source_url': chapter.guideline.url,
            }
        )
        
        if created:
            recommendation.topics.add(topic)
            self.stdout.write(f'Created recommendation: {recommendation.title}')
        
        return recommendation