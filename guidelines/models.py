"""
Optimized models for guidelines app - focused on performance.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Country(models.Model):
    """Country model with optimized indexing."""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.CharField(max_length=10, unique=True, db_index=True)
    
    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.flag_emoji} {self.name}"
    
    @property
    def flag_emoji(self):
        """Return flag emoji for country."""
        flag_map = {
            'UK': '🇬🇧',
            'ENG': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',  # England flag
            'SCT': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',  # Scotland flag
            'US': '🇺🇸', 
            'CA': '🇨🇦',
            'AU': '🇦🇺',
            'NZ': '🇳🇿',
            'FR': '🇫🇷',
            'DE': '🇩🇪',
            'IT': '🇮🇹',
            'ES': '🇪🇸',
            'NL': '🇳🇱',
            'SE': '🇸🇪',
            'NO': '🇳🇴',
            'DK': '🇩🇰',
            'FI': '🇫🇮',
            'JP': '🇯🇵',
            'KR': '🇰🇷',
            'CN': '🇨🇳',
            'IN': '🇮🇳',
            'BR': '🇧🇷',
            'MX': '🇲🇽',
        }
        return flag_map.get(self.code, '🏥')


class Organization(models.Model):
    """Healthcare organization."""
    name = models.CharField(max_length=200, db_index=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='organizations')
    website = models.URLField(blank=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.name} ({self.country.code})"


class Topic(models.Model):
    """Topic categories for recommendations."""
    name = models.CharField(max_length=255, unique=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
            models.Index(fields=['parent']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('guidelines:topic_detail', kwargs={'slug': self.slug})


class RecommendationStrength(models.Model):
    """Recommendation strength levels."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class EvidenceQuality(models.Model):
    """GRADE evidence quality levels."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Guideline(models.Model):
    """Clinical guidelines."""
    title = models.CharField(max_length=500, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='guidelines')
    publication_year = models.PositiveIntegerField(db_index=True)
    last_updated = models.DateField(null=True, blank=True)
    url = models.URLField(max_length=1000)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-publication_year', 'title']
        indexes = [
            models.Index(fields=['publication_year']),
            models.Index(fields=['is_active']),
            models.Index(fields=['organization']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.organization.country.code}, {self.publication_year})"

    def get_absolute_url(self):
        return reverse('guidelines:guideline_detail', kwargs={'pk': self.pk})


class Chapter(models.Model):
    """Guideline chapters."""
    guideline = models.ForeignKey(Guideline, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=500)
    number = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    
    class Meta:
        ordering = ['number']
        unique_together = ['guideline', 'number']

    def __str__(self):
        return f"Chapter {self.number}: {self.title}"


class Recommendation(models.Model):
    """Clinical recommendations - optimized for search and filtering."""
    title = models.CharField(max_length=500, db_index=True)
    text = models.TextField()
    guideline = models.ForeignKey(Guideline, on_delete=models.CASCADE, related_name='recommendations')
    chapter = models.ForeignKey(Chapter, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendations')
    topics = models.ManyToManyField(Topic, related_name='recommendations', blank=True)
    strength = models.ForeignKey(RecommendationStrength, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendations')
    evidence_quality = models.ForeignKey(EvidenceQuality, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendations')
    
    # Additional fields for enhanced search
    keywords = models.CharField(max_length=1000, blank=True, help_text="Comma-separated keywords for search")
    target_population = models.CharField(max_length=500, blank=True)
    clinical_context = models.CharField(max_length=500, blank=True)
    
    # URLs and metadata
    source_url = models.URLField(max_length=1000, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['strength']),
            models.Index(fields=['evidence_quality']),
            models.Index(fields=['guideline']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['keywords']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('guidelines:recommendation_detail', kwargs={'pk': self.pk})


class RecommendationReference(models.Model):
    """References for recommendations."""
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='references')
    text = models.TextField()
    url = models.URLField(max_length=1000, blank=True)
    pmid = models.CharField(max_length=20, blank=True, help_text="PubMed ID")
    doi = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Reference for {self.recommendation.title}"