"""
Forms for AI-powered personalized recommendations.
"""

from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """Form for collecting user profile information."""
    
    class Meta:
        model = UserProfile
        fields = [
            'age_group', 'location_country', 'caries_risk', 'periodontal_status',
            'fluoride_exposure', 'has_orthodontics', 'has_dental_implants',
            'has_diabetes', 'is_pregnant', 'has_dry_mouth', 'brushing_frequency',
            'flossing_frequency', 'diet_sugar_intake', 'specific_concerns', 'medications'
        ]
        
        widgets = {
            'age_group': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'location_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., United Kingdom, United States, Canada',
                'required': True
            }),
            'caries_risk': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'periodontal_status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'fluoride_exposure': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'has_orthodontics': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_dental_implants': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_diabetes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_pregnant': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_dry_mouth': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'brushing_frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., twice daily, once daily, rarely'
            }),
            'flossing_frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., daily, weekly, rarely'
            }),
            'diet_sugar_intake': forms.Select(attrs={
                'class': 'form-select'
            }),
            'specific_concerns': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any specific oral health concerns, symptoms, or questions you have...'
            }),
            'medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any medications you are currently taking...'
            }),
        }
        
        labels = {
            'age_group': 'Age Group',
            'location_country': 'Country/Location',
            'caries_risk': 'Dental Decay Risk Level',
            'periodontal_status': 'Gum Health Status',
            'fluoride_exposure': 'Fluoride Exposure',
            'has_orthodontics': 'Currently wearing braces or aligners',
            'has_dental_implants': 'Have dental implants',
            'has_diabetes': 'Have diabetes',
            'is_pregnant': 'Currently pregnant or nursing',
            'has_dry_mouth': 'Experience dry mouth symptoms',
            'brushing_frequency': 'Tooth Brushing Frequency',
            'flossing_frequency': 'Flossing Frequency',
            'diet_sugar_intake': 'Sugar Intake Level',
            'specific_concerns': 'Specific Oral Health Concerns',
            'medications': 'Current Medications',
        }
        
        help_texts = {
            'age_group': 'Select your age group for age-appropriate recommendations',
            'location_country': 'This helps us provide geographically relevant guidelines',
            'caries_risk': 'Based on your dental history and current oral health',
            'periodontal_status': 'Current condition of your gums',
            'fluoride_exposure': 'Select all sources of fluoride you are exposed to',
            'brushing_frequency': 'How often do you brush your teeth?',
            'flossing_frequency': 'How often do you floss or clean between teeth?',
            'diet_sugar_intake': 'Your typical consumption of sugary foods and drinks',
            'specific_concerns': 'Any pain, sensitivity, bleeding, or other concerns',
            'medications': 'Some medications can affect oral health',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['age_group'].required = True
        self.fields['location_country'].required = True
        self.fields['caries_risk'].required = True
        self.fields['periodontal_status'].required = True
        self.fields['fluoride_exposure'].required = True
    
    def clean_location_country(self):
        """Validate and normalize country input."""
        country = self.cleaned_data.get('location_country', '').strip()
        if not country:
            raise forms.ValidationError("Please enter your country or location.")
        
        # Normalize common country names
        country_mapping = {
            'uk': 'United Kingdom',
            'england': 'United Kingdom',
            'scotland': 'United Kingdom',
            'wales': 'United Kingdom',
            'northern ireland': 'United Kingdom',
            'usa': 'United States',
            'us': 'United States',
            'america': 'United States',
        }
        
        country_lower = country.lower()
        if country_lower in country_mapping:
            return country_mapping[country_lower]
        
        return country.title()
    
    def clean(self):
        """Additional form validation."""
        cleaned_data = super().clean()
        
        age_group = cleaned_data.get('age_group')
        is_pregnant = cleaned_data.get('is_pregnant')
        
        # Pregnancy validation
        if is_pregnant and age_group in ['0-2', '3-5', '6-12']:
            raise forms.ValidationError({
                'is_pregnant': 'Pregnancy status is not applicable for this age group.'
            })
        
        return cleaned_data