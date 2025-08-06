"""
Management command to scrape and update Cochrane review titles from the official website.
"""

import requests
import time
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from cochrane.models import CochraneReview


class Command(BaseCommand):
    help = 'Scrape and update Cochrane review titles from the official Cochrane Library'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit the number of reviews to update (0 = all)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between requests in seconds (default: 1.0)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update all reviews, even those with existing titles',
        )

    def handle(self, *args, **options):
        # Get reviews that need title updates
        if options['force']:
            reviews = CochraneReview.objects.all()
        else:
            # Only update reviews with generic titles
            reviews = CochraneReview.objects.filter(
                title__startswith='Cochrane Review CD'
            )
        
        if options['limit'] > 0:
            reviews = reviews[:options['limit']]
        
        total_reviews = reviews.count()
        self.stdout.write(f"Found {total_reviews} reviews to update")
        
        if total_reviews == 0:
            self.stdout.write(self.style.SUCCESS("No reviews need updating"))
            return
        
        updated_count = 0
        failed_count = 0
        
        for i, review in enumerate(reviews, 1):
            self.stdout.write(f"Processing {i}/{total_reviews}: {review.review_id}")
            
            try:
                # Scrape the title
                title = self.scrape_review_title(review.review_id)
                
                if title and title != review.title:
                    with transaction.atomic():
                        review.title = title
                        review.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Updated: {title[:60]}...")
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ No title found or same as existing")
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Failed: {str(e)}")
                )
                failed_count += 1
            
            # Add delay between requests
            if i < total_reviews:
                time.sleep(options['delay'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {updated_count} updated, {failed_count} failed"
            )
        )

    def scrape_review_title(self, review_code):
        """
        Scrape the title from multiple sources including Cochrane Library and PubMed.
        
        Args:
            review_code (str): The review code (e.g., 'CD000978')
            
        Returns:
            str: The scraped title or None if not found
        """
        # Try different sources and URL patterns
        sources = [
            # Cochrane Library direct URLs
            {
                'name': 'Cochrane Library',
                'urls': [
                    f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_code}.pub2/full",
                    f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_code}.pub3/full",
                    f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_code}/full",
                    f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_code}.pub1/full",
                ],
                'selectors': [
                    'h1.publication-title',
                    'h1[data-testid="publication-title"]', 
                    'h1.article-title',
                    '.publication-title h1',
                    'h1'
                ]
            },
            # Alternative Cochrane URLs
            {
                'name': 'Cochrane Abstract',
                'urls': [
                    f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_code}.pub2/abstract",
                    f"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.{review_code}/abstract",
                ],
                'selectors': [
                    'h1.publication-title',
                    'h1.article-title',
                    'h1'
                ]
            },
            # PubMed search as fallback
            {
                'name': 'PubMed',
                'urls': [
                    f"https://pubmed.ncbi.nlm.nih.gov/?term={review_code}+cochrane",
                ],
                'selectors': [
                    '.docsum-title',
                    'h1.heading-title',
                    '.article-title'
                ]
            }
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Use a session to maintain cookies
        session = requests.Session()
        session.headers.update(headers)
        
        for source in sources:
            self.stdout.write(f"    Trying source: {source['name']}")
            
            for url in source['urls']:
                try:
                    self.stdout.write(f"      URL: {url}")
                    response = session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Try the selectors for this source
                        for selector in source['selectors']:
                            title_element = soup.select_one(selector)
                            if title_element:
                                title = title_element.get_text().strip()
                                
                                # Clean up the title
                                title = self.clean_title(title)
                                
                                if title and len(title) > 10:
                                    # Additional validation for different sources
                                    if source['name'] == 'PubMed':
                                        # For PubMed, ensure it's actually a Cochrane review
                                        if 'cochrane' not in title.lower():
                                            continue
                                    
                                    if not title.startswith('Cochrane Review CD'):
                                        self.stdout.write(f"    ✓ Found title: {title[:60]}...")
                                        return title
                        
                        # If no title found with selectors, check page content
                        page_text = soup.get_text()
                        if 'Cochrane' in page_text:
                            self.stdout.write(f"      ⚠ Page found but no title extracted")
                        
                    elif response.status_code == 404:
                        self.stdout.write(f"      404 - Not found")
                    elif response.status_code == 403:
                        self.stdout.write(f"      403 - Access forbidden")
                    else:
                        self.stdout.write(f"      {response.status_code} - {response.reason}")
                        
                except requests.RequestException as e:
                    self.stdout.write(f"      Request error: {str(e)}")
                    continue
                except Exception as e:
                    self.stdout.write(f"      Parse error: {str(e)}")
                    continue
                
                # Add small delay between requests to be respectful
                time.sleep(0.5)
        
        return None

    def clean_title(self, title):
        """
        Clean and normalize the scraped title.
        
        Args:
            title (str): Raw title from the webpage
            
        Returns:
            str: Cleaned title
        """
        if not title:
            return None
        
        # Remove common prefixes and suffixes
        prefixes_to_remove = [
            'Cochrane Database of Systematic Reviews',
            'Cochrane Library',
            'Cochrane Review:',
            'Cochrane:',
        ]
        
        suffixes_to_remove = [
            '- Cochrane Library',
            '| Cochrane Library',
            'Cochrane Database of Systematic Reviews',
        ]
        
        # Clean the title
        cleaned = title.strip()
        
        # Remove prefixes
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove suffixes
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(cleaned.split())
        
        # Remove leading/trailing punctuation
        cleaned = cleaned.strip(' -|:')
        
        return cleaned if len(cleaned) > 5 else None