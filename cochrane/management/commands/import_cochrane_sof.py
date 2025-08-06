"""
Import Cochrane Summary of Findings data from CSV files.
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand
from cochrane.models import CochraneReview, CochraneSoFEntry
from datetime import datetime


class Command(BaseCommand):
    help = 'Import Cochrane Oral Health Summary of Findings from validated CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            'sof_directory',
            type=str,
            help='Path to the directory containing Cochrane SoF CSV files'
        )

    def handle(self, *args, **options):
        sof_directory = os.path.expanduser(options['sof_directory'])
        
        if not os.path.isdir(sof_directory):
            self.stdout.write(self.style.ERROR(f"Directory not found: {sof_directory}"))
            return

        for root, dirs, files in os.walk(sof_directory):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    review_id = os.path.basename(root)
                    
                    try:
                        df = pd.read_csv(file_path)
                        
                        review, created = CochraneReview.objects.get_or_create(
                            review_id=review_id,
                            defaults={
                                'title': f"Cochrane Review {review_id}",
                                'url': f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_id}.pub2/full",
                                'publication_date': datetime.now().date(),
                            }
                        )
                        
                        for index, row in df.iterrows():
                            significant = None
                            if pd.notna(row.get('Significant')):
                                significant = str(row['Significant']).lower() == 'true'

                            risk_of_bias = None
                            if pd.notna(row.get('Risk of bias')):
                                risk_of_bias = str(row['Risk of bias']).lower() == 'true'

                            imprecision = None
                            if pd.notna(row.get('Imprecision')):
                                imprecision = str(row['Imprecision']).lower() == 'true'

                            inconsistency = None
                            if pd.notna(row.get('Inconsistency')):
                                inconsistency = str(row['Inconsistency']).lower() == 'true'

                            indirectness = None
                            if pd.notna(row.get('Indirectness')):
                                indirectness = str(row['Indirectness']).lower() == 'true'

                            publication_bias = None
                            if pd.notna(row.get('Publication bias')):
                                publication_bias = str(row['Publication bias']).lower() == 'true'

                            CochraneSoFEntry.objects.create(
                                review=review,
                                population=row.get('Population'),
                                intervention=row.get('Intervention'),
                                comparison=row.get('Comparison'),
                                outcome=row.get('Outcome'),
                                measure=row.get('Measure'),
                                effect=row.get('Effect'),
                                ci_lower=str(row.get('CI Lower')) if pd.notna(row.get('CI Lower')) else None,
                                ci_upper=str(row.get('CI Upper')) if pd.notna(row.get('CI Upper')) else None,
                                significant=significant,
                                num_participants=str(row.get('Number of participants')) if pd.notna(row.get('Number of participants')) else None,
                                num_studies=str(row.get('Number of studies')) if pd.notna(row.get('Number of studies')) else None,
                                certainty_of_evidence=row.get('Certainty of the evidence (GRADE)'),
                                reasons_for_grade=row.get('Reasons for GRADE if not High'),
                                risk_of_bias=risk_of_bias,
                                imprecision=imprecision,
                                inconsistency=inconsistency,
                                indirectness=indirectness,
                                publication_bias=publication_bias,
                            )
                        
                        self.stdout.write(f'Imported {len(df)} entries for {review_id}')
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing {file_path}: {e}'))

        self.stdout.write(self.style.SUCCESS('Finished importing Cochrane SoF data'))