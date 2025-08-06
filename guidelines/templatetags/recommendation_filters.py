"""
Custom template filters for recommendation formatting.
"""
import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.filter
def parse_recommendation_text(text):
    """
    Parse recommendation text to handle bullet points, formatting, and structure.
    
    Handles:
    - Bullet points with • or -
    - Numbered lists
    - Multiple sentences
    - Proper paragraphs
    """
    if not text:
        return ""
    
    # Escape HTML first
    text = escape(text)
    
    # Split by major separators (periods followed by bullet points or new sections)
    sections = []
    current_section = ""
    
    # Split the text into sentences and bullet points
    # Look for patterns like ". •" or ": •" which indicate bullet point starts
    parts = re.split(r'(\. •|: •|\n•|^•)', text)
    
    formatted_parts = []
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
            
        # Check if this is a bullet point separator
        if part in ['. •', ': •', '\n•', '^•']:
            continue
            
        # Check if this part starts with a bullet point
        if part.startswith('•') or part.startswith('-') or part.startswith('*'):
            # This is a bullet point
            bullet_text = part[1:].strip()
            formatted_parts.append(f'<li>{bullet_text}</li>')
        elif re.match(r'^\d+\.', part):
            # This is a numbered list item
            numbered_text = re.sub(r'^\d+\.\s*', '', part)
            formatted_parts.append(f'<li>{numbered_text}</li>')
        else:
            # Check if previous parts were list items
            if formatted_parts and formatted_parts[-1].startswith('<li>'):
                # Continue the list
                formatted_parts.append(f'<li>{part}</li>')
            else:
                # This is regular text
                if part.endswith(':') and i < len(parts) - 1:
                    # This might be introducing a list
                    formatted_parts.append(f'<p><strong>{part}</strong></p>')
                else:
                    formatted_parts.append(f'<p>{part}</p>')
    
    # If we didn't find any special formatting, try a different approach
    if len(formatted_parts) <= 1:
        # Split by bullet points more aggressively
        if '•' in text or '–' in text or '-' in text:
            # Split the text into main text and bullet points
            parts = re.split(r'(•|–|-)', text)
            main_text = ""
            bullet_points = []
            
            current_bullet = ""
            in_bullets = False
            
            for part in parts:
                part = part.strip()
                if part in ['•', '–', '-']:
                    if main_text and not in_bullets:
                        # This is the start of bullet points
                        in_bullets = True
                    elif current_bullet:
                        # Save previous bullet and start new one
                        bullet_points.append(current_bullet.strip())
                        current_bullet = ""
                elif not in_bullets:
                    main_text += part + " "
                else:
                    current_bullet += part + " "
            
            # Add the last bullet point
            if current_bullet:
                bullet_points.append(current_bullet.strip())
            
            # Format the result
            result = ""
            if main_text.strip():
                result += f'<p class="lead mb-3">{main_text.strip()}</p>'
            
            if bullet_points:
                result += '<ul class="recommendation-bullets">'
                for bullet in bullet_points:
                    if bullet.strip():
                        result += f'<li>{bullet.strip()}</li>'
                result += '</ul>'
            
            if result:
                return mark_safe(result)
    
    # Wrap list items in ul tags
    result = ""
    in_list = False
    
    for part in formatted_parts:
        if part.startswith('<li>'):
            if not in_list:
                result += '<ul class="recommendation-bullets">'
                in_list = True
            result += part
        else:
            if in_list:
                result += '</ul>'
                in_list = False
            result += part
    
    if in_list:
        result += '</ul>'
    
    # If still no special formatting, just return as paragraphs
    if not result or result == text:
        # Split by sentences and create paragraphs
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            result = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    result += f'<p>{sentence}</p>'
        else:
            result = f'<p class="lead">{text}</p>'
    
    return mark_safe(result)


@register.filter
def format_evidence_quality(quality):
    """Format evidence quality with appropriate styling."""
    if not quality:
        return mark_safe('<span class="text-muted">Not assessed</span>')
    
    quality_str = str(quality).lower()
    
    if quality_str == 'high':
        return mark_safe(f'<span class="badge bg-success fs-6"><i class="fas fa-star me-1"></i>{quality}</span>')
    elif quality_str == 'moderate':
        return mark_safe(f'<span class="badge bg-primary fs-6"><i class="fas fa-star-half-alt me-1"></i>{quality}</span>')
    elif quality_str == 'low':
        return mark_safe(f'<span class="badge bg-warning text-dark fs-6"><i class="fas fa-exclamation-triangle me-1"></i>{quality}</span>')
    elif quality_str in ['very low', 'very_low']:
        return mark_safe(f'<span class="badge bg-danger fs-6"><i class="fas fa-times-circle me-1"></i>{quality}</span>')
    else:
        return mark_safe(f'<span class="badge bg-secondary fs-6">{quality}</span>')


@register.filter
def format_recommendation_strength(strength):
    """Format recommendation strength with appropriate styling."""
    if not strength:
        return mark_safe('<span class="text-muted">Not assessed</span>')
    
    strength_str = str(strength).lower()
    
    if strength_str == 'strong':
        return mark_safe(f'<span class="badge bg-success fs-6"><i class="fas fa-thumbs-up me-1"></i>{strength}</span>')
    elif strength_str == 'moderate':
        return mark_safe(f'<span class="badge bg-primary fs-6"><i class="fas fa-hand-paper me-1"></i>{strength}</span>')
    elif strength_str == 'weak':
        return mark_safe(f'<span class="badge bg-warning text-dark fs-6"><i class="fas fa-hand-point-right me-1"></i>{strength}</span>')
    else:
        return mark_safe(f'<span class="badge bg-secondary fs-6">{strength}</span>')