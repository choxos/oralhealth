"""
Management command to populate the database with UK oral health guidelines.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from guidelines.models import (
    Country, Organization, Guideline, Chapter, Topic,
    RecommendationStrength, EvidenceQuality, Recommendation, Reference
)


class Command(BaseCommand):
    help = 'Populate database with UK oral health guidelines from Delivering Better Oral Health'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting UK guidelines population...'))
        
        with transaction.atomic():
            # Create countries
            uk, created = Country.objects.get_or_create(
                code='UK',
                defaults={
                    'name': 'United Kingdom',
                    'flag_emoji': '🇬🇧'
                }
            )
            if created:
                self.stdout.write(f'Created country: {uk.name}')
            
            # Create organization
            ohid, created = Organization.objects.get_or_create(
                name='Office for Health Improvement & Disparities',
                country=uk,
                defaults={
                    'website': 'https://www.gov.uk/government/organisations/office-for-health-improvement-and-disparities',
                    'description': 'UK government department responsible for public health policy'
                }
            )
            if created:
                self.stdout.write(f'Created organization: {ohid.name}')
            
            # Create recommendation strengths
            strengths = [
                ('Strong Recommendation', 'STRONG', 'Evidence-based strong recommendation', 'oralhealth-strength-strong'),
                ('Weak Recommendation', 'WEAK', 'Evidence-based weak recommendation', 'oralhealth-strength-weak'),
                ('Good Practice Point', 'GPP', 'Good practice recommendation', 'oralhealth-strength-good-practice'),
            ]
            
            for name, code, desc, color_class in strengths:
                strength, created = RecommendationStrength.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'description': desc,
                        'color_class': color_class
                    }
                )
                if created:
                    self.stdout.write(f'Created strength: {strength.name}')
            
            # Create evidence qualities
            qualities = [
                ('High Quality', 'HIGH', 'High certainty evidence', 'oralhealth-evidence-high'),
                ('Moderate Quality', 'MODERATE', 'Moderate certainty evidence', 'oralhealth-evidence-moderate'),
                ('Low Quality', 'LOW', 'Low certainty evidence', 'oralhealth-evidence-low'),
                ('Very Low Quality', 'VERY_LOW', 'Very low certainty evidence', 'oralhealth-evidence-very-low'),
            ]
            
            for name, grade, desc, color_class in qualities:
                quality, created = EvidenceQuality.objects.get_or_create(
                    grade=grade,
                    defaults={
                        'name': name,
                        'description': desc,
                        'color_class': color_class
                    }
                )
                if created:
                    self.stdout.write(f'Created evidence quality: {quality.name}')
            
            # Create topics
            topics_data = [
                ('Dental Caries', 'Prevention and management of tooth decay'),
                ('Periodontal Diseases', 'Prevention and management of gum diseases'),
                ('Oral Cancer', 'Prevention and early detection of oral cancer'),
                ('Tooth Wear', 'Prevention and management of tooth wear'),
                ('Oral Hygiene', 'Toothbrushing and oral hygiene practices'),
                ('Fluoride', 'Use of fluoride in oral health prevention'),
                ('Healthier Eating', 'Dietary advice for oral health'),
                ('Smoking and Tobacco', 'Tobacco cessation for oral health'),
                ('Alcohol', 'Alcohol advice for oral health'),
                ('Behaviour Change', 'Supporting patient behaviour change'),
            ]
            
            for name, desc in topics_data:
                topic, created = Topic.objects.get_or_create(
                    name=name,
                    defaults={'description': desc}
                )
                if created:
                    self.stdout.write(f'Created topic: {topic.name}')
            
            # Create main guideline
            guideline, created = Guideline.objects.get_or_create(
                title='Delivering better oral health: an evidence-based toolkit for prevention',
                organization=ohid,
                defaults={
                    'publication_year': 2021,
                    'version': '4th Edition',
                    'url': 'https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention',
                    'description': 'Evidence-based toolkit for dental teams to improve oral health prevention',
                    'last_updated': '2021-11-09',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created guideline: {guideline.title}')
            
            # Create sample recommendations for demonstration
            sample_recommendations = [
                {
                    'title': 'Toothbrushing frequency and timing',
                    'text': 'Brush teeth twice daily with fluoride toothpaste, last thing at night and at least one other time during the day.',
                    'strength': 'STRONG',
                    'evidence_quality': 'HIGH',
                    'topic': 'Oral Hygiene',
                    'target_population': 'All ages',
                    'keywords': 'toothbrushing, fluoride, oral hygiene, prevention',
                },
                {
                    'title': 'Fluoride toothpaste concentration for children',
                    'text': 'Children should use toothpaste containing at least 1,000 ppm fluoride. Family toothpaste (1,350-1,500 ppm) is recommended for maximum caries prevention except where children cannot prevent swallowing.',
                    'strength': 'STRONG',
                    'evidence_quality': 'HIGH',
                    'topic': 'Fluoride',
                    'target_population': 'Children',
                    'keywords': 'fluoride, toothpaste, children, caries prevention',
                },
                {
                    'title': 'Smoking cessation advice',
                    'text': 'All patients should be asked about tobacco use and offered brief intervention advice to quit smoking.',
                    'strength': 'STRONG',
                    'evidence_quality': 'MODERATE',
                    'topic': 'Smoking and Tobacco',
                    'target_population': 'Adult smokers',
                    'keywords': 'smoking, tobacco, cessation, brief intervention',
                },
            ]
            
            for rec_data in sample_recommendations:
                topic = Topic.objects.get(name=rec_data['topic'])
                strength = RecommendationStrength.objects.get(code=rec_data['strength'])
                evidence_quality = EvidenceQuality.objects.get(grade=rec_data['evidence_quality'])
                
                recommendation, created = Recommendation.objects.get_or_create(
                    title=rec_data['title'],
                    guideline=guideline,
                    defaults={
                        'text': rec_data['text'],
                        'strength': strength,
                        'evidence_quality': evidence_quality,
                        'target_population': rec_data['target_population'],
                        'keywords': rec_data['keywords'],
                        'guideline_url': f"{guideline.url}/chapter-{topic.name.lower().replace(' ', '-')}",
                    }
                )
                
                if created:
                    recommendation.topics.add(topic)
                    self.stdout.write(f'Created recommendation: {recommendation.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated UK guidelines data!')
        )