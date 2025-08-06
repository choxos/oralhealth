"""
Management command to import Cochrane review titles from a CSV file.
This is an alternative to web scraping when automated access is restricted.
"""

import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from cochrane.models import CochraneReview


class Command(BaseCommand):
    help = 'Import Cochrane review titles from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file with columns: review_code,title',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                updated_count = 0
                not_found_count = 0
                skipped_count = 0
                
                for row in reader:
                    review_code = row.get('review_code', '').strip()
                    title = row.get('title', '').strip()
                    
                    if not review_code or not title:
                        self.stdout.write(
                            self.style.WARNING(f"Skipping row with missing data: {row}")
                        )
                        skipped_count += 1
                        continue
                    
                    try:
                        review = CochraneReview.objects.get(review_id=review_code)
                        
                        if review.title != title:
                            self.stdout.write(f"Updating {review_code}: {title[:60]}...")
                            
                            if not dry_run:
                                with transaction.atomic():
                                    review.title = title
                                    review.save()
                            
                            updated_count += 1
                        else:
                            self.stdout.write(f"Same title for {review_code}, skipping")
                            skipped_count += 1
                            
                    except CochraneReview.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f"Review {review_code} not found in database")
                        )
                        not_found_count += 1
                
                # Summary
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nCompleted: {updated_count} updated, "
                        f"{skipped_count} skipped, {not_found_count} not found"
                    )
                )
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING("No changes were made (dry run mode)")
                    )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"File not found: {csv_file}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error processing file: {str(e)}")
            )