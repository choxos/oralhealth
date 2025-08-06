"""
Models for oral health guidelines and recommendations.
Supports UK, US, Canada, Australia, and New Zealand guidelines.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Country(models.Model):
    """Countries that have oral health guidelines."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # UK, US, CA, AU, NZ
    flag_emoji = models.CharField(max_length=10, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Countries'
    
    def __str__(self):
        return self.name


class Organization(models.Model):
    """Organizations that publish oral health guidelines."""
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['country', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.country.code})"


class Guideline(models.Model):
    """Oral health guidelines from various countries."""
    title = models.CharField(max_length=500)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    publication_year = models.PositiveIntegerField()
    version = models.CharField(max_length=50, blank=True)
    url = models.URLField()
    description = models.TextField()
    last_updated = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-publication_year', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.organization.country.code} {self.publication_year})"
    
    def get_absolute_url(self):
        return reverse('guidelines:guideline_detail', kwargs={'pk': self.pk})


class Chapter(models.Model):
    """Chapters within guidelines."""
    guideline = models.ForeignKey(Guideline, on_delete=models.CASCADE, related_name='chapters')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=500)
    url = models.URLField(blank=True)
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    class Meta:
        ordering = ['guideline', 'number']
        unique_together = ['guideline', 'number']
    
    def __str__(self):
        return f"{self.guideline.title} - Chapter {self.number}: {self.title}"


class Topic(models.Model):
    """Topics covered in oral health recommendations."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtopics')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('guidelines:topic_detail', kwargs={'slug': self.slug})


class RecommendationStrength(models.Model):
    """Strength of recommendations (Strong, Weak, Good Practice Point)."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)  # STRONG, WEAK, GPP
    description = models.TextField()
    color_class = models.CharField(max_length=50, help_text="CSS class for styling")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EvidenceQuality(models.Model):
    """Quality of evidence using GRADE system."""
    name = models.CharField(max_length=100, unique=True)
    grade = models.CharField(max_length=20, unique=True)  # HIGH, MODERATE, LOW, VERY_LOW
    description = models.TextField()
    color_class = models.CharField(max_length=50, help_text="CSS class for styling")
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Evidence Qualities'
    
    def __str__(self):
        return self.name


class Recommendation(models.Model):
    """Individual recommendations from oral health guidelines."""
    title = models.CharField(max_length=500)
    text = models.TextField()
    guideline = models.ForeignKey(Guideline, on_delete=models.CASCADE, related_name='recommendations')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name='recommendations')
    topics = models.ManyToManyField(Topic, related_name='recommendations')
    
    # Recommendation metadata
    strength = models.ForeignKey(RecommendationStrength, on_delete=models.CASCADE)
    evidence_quality = models.ForeignKey(EvidenceQuality, on_delete=models.CASCADE)
    
    # Population and context
    target_population = models.CharField(max_length=500, blank=True)
    age_group = models.CharField(max_length=200, blank=True)
    clinical_context = models.TextField(blank=True)
    
    # URLs and references
    guideline_url = models.URLField(blank=True, help_text="Direct link to this recommendation in the guideline")
    page_number = models.CharField(max_length=50, blank=True)
    
    # Search and filtering
    keywords = models.TextField(blank=True, help_text="Keywords for search, comma-separated")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.guideline.organization.country.code})"
    
    def get_absolute_url(self):
        return reverse('guidelines:recommendation_detail', kwargs={'pk': self.pk})
    
    def get_search_keywords(self):
        """Get keywords as a list."""
        if self.keywords:
            return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
        return []


class Reference(models.Model):
    """References supporting recommendations."""
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='references')
    title = models.CharField(max_length=500)
    authors = models.TextField(blank=True)
    journal = models.CharField(max_length=200, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=100, blank=True)
    doi = models.CharField(max_length=200, blank=True)
    pmid = models.CharField(max_length=50, blank=True)
    url = models.URLField(blank=True)
    reference_type = models.CharField(max_length=100, default='Journal Article')
    
    class Meta:
        ordering = ['year', 'title']
    
    def __str__(self):
        return self.title
    
    def get_citation(self):
        """Generate a formatted citation."""
        citation_parts = []
        if self.authors:
            citation_parts.append(self.authors)
        if self.title:
            citation_parts.append(self.title)
        if self.journal and self.year:
            journal_part = f"{self.journal}. {self.year}"
            if self.volume:
                journal_part += f";{self.volume}"
            if self.pages:
                journal_part += f":{self.pages}"
            citation_parts.append(journal_part)
        return '. '.join(citation_parts) + '.'