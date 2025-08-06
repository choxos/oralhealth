"""
Optimized models for Cochrane Oral Health reviews.
"""

from django.db import models
from django.urls import reverse


class CochraneReview(models.Model):
    """Cochrane Oral Health systematic reviews."""
    review_id = models.CharField(max_length=50, unique=True, db_index=True, help_text="e.g., CD000979")
    title = models.CharField(max_length=1000)
    url = models.URLField(max_length=1000, blank=True, null=True)
    publication_date = models.DateField(null=True, blank=True)
    authors = models.CharField(max_length=500, blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-publication_date', 'title']
        indexes = [
            models.Index(fields=['review_id']),
            models.Index(fields=['-publication_date']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('cochrane:cochrane_review_detail', kwargs={'review_id': self.review_id})


class CochraneSoFEntry(models.Model):
    """Summary of Findings entries from Cochrane reviews."""
    review = models.ForeignKey(CochraneReview, on_delete=models.CASCADE, related_name='sof_entries')
    population = models.TextField(blank=True, null=True)
    intervention = models.TextField(blank=True, null=True)
    comparison = models.TextField(blank=True, null=True)
    outcome = models.TextField(blank=True, null=True)
    measure = models.CharField(max_length=255, blank=True, null=True)
    effect = models.CharField(max_length=255, blank=True, null=True)
    ci_lower = models.CharField(max_length=255, blank=True, null=True)
    ci_upper = models.CharField(max_length=255, blank=True, null=True)
    significant = models.BooleanField(null=True, blank=True)
    num_participants = models.CharField(max_length=255, blank=True, null=True)
    num_studies = models.CharField(max_length=255, blank=True, null=True)
    certainty_of_evidence = models.CharField(max_length=50, blank=True, null=True)
    reasons_for_grade = models.TextField(blank=True, null=True)
    risk_of_bias = models.BooleanField(null=True, blank=True)
    imprecision = models.BooleanField(null=True, blank=True)
    inconsistency = models.BooleanField(null=True, blank=True)
    indirectness = models.BooleanField(null=True, blank=True)
    publication_bias = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cochrane SoF Entries"
        ordering = ['review', 'id']
        indexes = [
            models.Index(fields=['review']),
            models.Index(fields=['certainty_of_evidence']),
        ]

    def __str__(self):
        return f"SoF for {self.review.title} - Outcome: {self.outcome}"