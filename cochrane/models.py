"""
Models for Cochrane Oral Health reviews and Summary of Findings tables.
"""

from django.db import models
from django.urls import reverse


class CochraneReview(models.Model):
    """Cochrane Oral Health systematic reviews."""
    cochrane_id = models.CharField(max_length=20, unique=True, help_text="e.g., CD000979")
    title = models.CharField(max_length=500)
    authors = models.TextField()
    publication_year = models.PositiveIntegerField()
    last_updated = models.DateField()
    doi = models.CharField(max_length=200, blank=True)
    url = models.URLField()
    abstract = models.TextField()
    
    # Review metadata
    review_type = models.CharField(max_length=100, default='Intervention')
    status = models.CharField(max_length=50, default='Published')
    
    class Meta:
        ordering = ['-last_updated', 'title']
    
    def __str__(self):
        return f"{self.cochrane_id}: {self.title}"
    
    def get_absolute_url(self):
        return reverse('cochrane:review_detail', kwargs={'cochrane_id': self.cochrane_id})


class SummaryOfFindings(models.Model):
    """Summary of Findings tables from Cochrane reviews."""
    review = models.ForeignKey(CochraneReview, on_delete=models.CASCADE, related_name='sof_tables')
    comparison_title = models.CharField(max_length=500)
    population = models.TextField()
    intervention = models.TextField()
    comparison = models.TextField()
    
    class Meta:
        ordering = ['review', 'comparison_title']
        verbose_name_plural = 'Summary of Findings'
    
    def __str__(self):
        return f"{self.review.cochrane_id} - {self.comparison_title}"


class Outcome(models.Model):
    """Individual outcomes in Summary of Findings tables."""
    sof_table = models.ForeignKey(SummaryOfFindings, on_delete=models.CASCADE, related_name='outcomes')
    outcome_name = models.CharField(max_length=500)
    measure = models.CharField(max_length=100, help_text="OR, RR, MD, etc.")
    effect = models.CharField(max_length=100, blank=True)
    ci_lower = models.CharField(max_length=100, blank=True)
    ci_upper = models.CharField(max_length=100, blank=True)
    significant = models.BooleanField(null=True, blank=True)
    
    # Study information
    number_of_participants = models.PositiveIntegerField(null=True, blank=True)
    number_of_studies = models.PositiveIntegerField(null=True, blank=True)
    
    # GRADE assessment
    certainty_of_evidence = models.CharField(max_length=50, blank=True)
    grade_reasons = models.TextField(blank=True)
    
    # Risk of bias components
    risk_of_bias = models.BooleanField(null=True, blank=True)
    imprecision = models.BooleanField(null=True, blank=True)
    inconsistency = models.BooleanField(null=True, blank=True)
    indirectness = models.BooleanField(null=True, blank=True)
    publication_bias = models.BooleanField(null=True, blank=True)
    
    class Meta:
        ordering = ['sof_table', 'outcome_name']
    
    def __str__(self):
        return f"{self.sof_table.review.cochrane_id} - {self.outcome_name}"
    
    def get_confidence_interval(self):
        """Get formatted confidence interval."""
        if self.ci_lower and self.ci_upper:
            return f"[{self.ci_lower}, {self.ci_upper}]"
        return ""
    
    def get_grade_class(self):
        """Get CSS class for GRADE certainty."""
        if not self.certainty_of_evidence:
            return ""
        
        certainty_lower = self.certainty_of_evidence.lower()
        if 'high' in certainty_lower:
            return 'oralhealth-evidence-high'
        elif 'moderate' in certainty_lower:
            return 'oralhealth-evidence-moderate'
        elif 'low' in certainty_lower and 'very' not in certainty_lower:
            return 'oralhealth-evidence-low'
        elif 'very low' in certainty_lower:
            return 'oralhealth-evidence-very-low'
        return ""