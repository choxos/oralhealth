"""
Forms for the guidelines app.
"""

from django import forms
from .models import Country, Topic, RecommendationStrength, EvidenceQuality


class RecommendationSearchForm(forms.Form):
    """Form for searching and filtering recommendations."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search recommendations...',
            'class': 'xera-input',
        })
    )
    
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        empty_label="All Countries",
        widget=forms.Select(attrs={
            'class': 'xera-select',
        })
    )
    
    topic = forms.ModelChoiceField(
        queryset=Topic.objects.filter(parent=None),
        required=False,
        empty_label="All Topics",
        widget=forms.Select(attrs={
            'class': 'xera-select',
        })
    )
    
    strength = forms.ModelChoiceField(
        queryset=RecommendationStrength.objects.all(),
        required=False,
        empty_label="All Strengths",
        widget=forms.Select(attrs={
            'class': 'xera-select',
        })
    )
    
    evidence_quality = forms.ModelChoiceField(
        queryset=EvidenceQuality.objects.all(),
        required=False,
        empty_label="All Evidence Quality",
        widget=forms.Select(attrs={
            'class': 'xera-select',
        })
    )