from django.core.management.base import BaseCommand
import json as stdlib_json
import os
from pathlib import Path
from guidelines.models import (
    Country, Guideline, Topic, Recommendation, 
    RecommendationReference
)
from cochrane.models import CochraneReview, CochraneSoFEntry

class Command(BaseCommand):
    help = 'Load guidelines and Cochrane data from JSON files'

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        # Load UK Guidelines
        self.load_uk_guidelines(base_dir)
        
        # Load Cochrane SoF data
        self.load_cochrane_sof(base_dir)

    def load_uk_guidelines(self, base_dir):
        json_file = base_dir / "data" / "uk_guidelines" / "uk_guidelines.json"
        
        if not json_file.exists():
            self.stdout.write(self.style.ERROR(f"JSON file not found: {json_file}"))
            return
            
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
            data = stdlib_json.loads(content)
        
        # Create country
        country, created = Country.objects.get_or_create(
            name=data['country'],
            defaults={'code': 'UK'}
        )
        
        # Create organization
        org, created = Organization.objects.get_or_create(
            name=data['organization'],
            country=country,
            defaults={'website': 'https://www.gov.uk'}
        )
        
        # Create guideline
        guideline, created = Guideline.objects.get_or_create(
            title=data['guideline_title'],
            organization=org,
            defaults={
                'publication_year': data['year'],
                'url': data['source_url']
            }
        )
        
        recommendation_count = 0
        
        for rec_data in data['recommendations']:
            # Create topic
            topic, created = Topic.objects.get_or_create(
                name=rec_data['topic']
            )
            
            # Create recommendation
            recommendation, created = Recommendation.objects.get_or_create(
                text=rec_data['text'],
                defaults={
                    'guideline': guideline,
                    'topic': topic,
                    'strength': rec_data['strength'],
                    'evidence_quality': rec_data['evidence_quality']
                }
            )
            
            if created:
                # Create reference
                RecommendationReference.objects.get_or_create(
                    recommendation=recommendation,
                    defaults={
                        'title': f"{rec_data.get('table_context', 'UK Guidelines')} - {data['guideline_title']}",
                        'url': rec_data['source_url'],
                        'citation': f"{data['organization']} ({data['year']}). {rec_data.get('table_context', 'Evidence Tables')}."
                    }
                )
                recommendation_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {recommendation_count} recommendations from UK guidelines')
        )

    def load_cochrane_sof(self, base_dir):
        json_file = base_dir / "data" / "cochrane_sof" / "cochrane_sof.json"
        
        if not json_file.exists():
            self.stdout.write(self.style.WARNING(f"Cochrane JSON file not found: {json_file}"))
            return
            
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
            data = stdlib_json.loads(content)
        
        review_count = 0
        entry_count = 0
        
        for review_data in data['reviews']:
            # Create review
            review, created = CochraneReview.objects.get_or_create(
                review_id=review_data['review_id'],
                defaults={
                    'title': f"Cochrane Review {review_data['review_id']}",
                    'url': f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_data['review_id']}/full"
                }
            )
            
            if created:
                review_count += 1
            
            for sof_data in review_data['sof_entries']:
                # Create SoF entry
                sof_entry, created = CochraneSoFEntry.objects.get_or_create(
                    review=review,
                    outcome=sof_data['outcome'],
                    defaults={
                        'intervention': sof_data['intervention'],
                        'comparison': sof_data['comparison'],
                        'participants': sof_data['participants'],
                        'studies': sof_data['studies'],
                        'effect': sof_data['effect'],
                        'certainty': sof_data['certainty'],
                        'comments': sof_data['comments']
                    }
                )
                
                if created:
                    entry_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {review_count} reviews and {entry_count} SoF entries')
        )