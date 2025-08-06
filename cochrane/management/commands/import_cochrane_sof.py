"""
Management command to import Cochrane SoF data from CSV files.
"""

import os
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from cochrane.models import CochraneReview, SummaryOfFindings, Outcome


class Command(BaseCommand):
    help = 'Import Cochrane Summary of Findings data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            default='/Users/choxos/Documents/Github/CoE-Cochrane/validated/SoF',
            help='Directory containing Cochrane SoF CSV files'
        )

    def handle(self, *args, **options):
        directory = options['directory']
        self.stdout.write(f'Starting import from: {directory}')
        
        if not os.path.exists(directory):
            self.stderr.write(f'Directory does not exist: {directory}')
            return
        
        imported_count = 0
        
        # Iterate through each Cochrane ID directory
        for cochrane_dir in os.listdir(directory):
            if not cochrane_dir.startswith('CD'):
                continue
                
            cochrane_path = os.path.join(directory, cochrane_dir)
            if not os.path.isdir(cochrane_path):
                continue
            
            self.stdout.write(f'Processing {cochrane_dir}...')
            
            # Find the latest CSV file in the directory
            csv_files = [f for f in os.listdir(cochrane_path) if f.endswith('.csv')]
            if not csv_files:
                self.stdout.write(f'No CSV files found in {cochrane_dir}')
                continue
            
            # Sort by version (PUB3 > PUB2, etc.)
            csv_files.sort(reverse=True)
            latest_csv = csv_files[0]
            csv_path = os.path.join(cochrane_path, latest_csv)
            
            try:
                with transaction.atomic():
                    self.import_review_data(cochrane_dir, csv_path)
                    imported_count += 1
            except Exception as e:
                self.stderr.write(f'Error importing {cochrane_dir}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported_count} Cochrane reviews')
        )

    def import_review_data(self, cochrane_id, csv_path):
        """Import data for a single Cochrane review."""
        
        # Create or get the review (placeholder data)
        review, created = CochraneReview.objects.get_or_create(
            cochrane_id=cochrane_id,
            defaults={
                'title': f'Cochrane Review {cochrane_id}',
                'authors': 'Multiple authors',
                'publication_year': 2020,
                'last_updated': '2020-01-01',
                'url': f'https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{cochrane_id}.pub3/full',
                'abstract': 'Cochrane systematic review of oral health interventions.',
            }
        )
        
        if created:
            self.stdout.write(f'Created review: {review.cochrane_id}')
        
        # Read and import CSV data
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            current_sof = None
            current_comparison = ""
            
            for row in reader:
                # Extract key fields
                population = row.get('Population', '')
                intervention = row.get('Intervention', '')
                comparison = row.get('Comparison', '')
                outcome = row.get('Outcome', '')
                
                # Create comparison key
                comparison_key = f"{intervention} vs {comparison}"
                
                # Create SoF table if needed
                if comparison_key != current_comparison:
                    current_sof, _ = SummaryOfFindings.objects.get_or_create(
                        review=review,
                        comparison_title=comparison_key,
                        defaults={
                            'population': population,
                            'intervention': intervention,
                            'comparison': comparison,
                        }
                    )
                    current_comparison = comparison_key
                
                # Create outcome
                outcome_obj = Outcome.objects.create(
                    sof_table=current_sof,
                    outcome_name=outcome,
                    measure=row.get('Measure', ''),
                    effect=row.get('Effect', ''),
                    ci_lower=row.get('CI Lower', ''),
                    ci_upper=row.get('CI Upper', ''),
                    significant=self.parse_boolean(row.get('Significant')),
                    number_of_participants=self.parse_integer(row.get('Number of participants')),
                    number_of_studies=self.parse_integer(row.get('Number of studies')),
                    certainty_of_evidence=row.get('Certainty of the evidence (GRADE)', ''),
                    grade_reasons=row.get('Reasons for GRADE if not High', ''),
                    risk_of_bias=self.parse_boolean(row.get('Risk of bias')),
                    imprecision=self.parse_boolean(row.get('Imprecision')),
                    inconsistency=self.parse_boolean(row.get('Inconsistency')),
                    indirectness=self.parse_boolean(row.get('Indirectness')),
                    publication_bias=self.parse_boolean(row.get('Publication bias')),
                )
    
    def parse_boolean(self, value):
        """Parse boolean values from CSV."""
        if not value or value.upper() in ['NA', 'N/A', '']:
            return None
        return value.upper() in ['TRUE', 'YES', '1']
    
    def parse_integer(self, value):
        """Parse integer values from CSV."""
        if not value or value.upper() in ['NA', 'N/A', '']:
            return None
        try:
            return int(value)
        except ValueError:
            return None