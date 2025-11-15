from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='mathformat')
def mathformat(text):
    if not text:
        return text

    text = str(text)
    original_text = text

    # If already wrapped in LaTeX delimiters, return as-is
    if text.strip().startswith('$') and text.strip().endswith('$'):
        return mark_safe(text)

    # Wrap content that has LaTeX commands
    if '\\begin{' in text or '\\frac{' in text or '\\sqrt{' in text or '\\end{' in text:
        if not text.strip().startswith('$'):
            text = f"${text}$"
        return mark_safe(text)

    # Pattern for matrix variables: A32, A23, etc (subscript notation)
    text = re.sub(r'\b([A-Z])(\d{2})\b', r'$\1_{\2}$', text)

    # Pattern for simple variable subscripts: A1, A2, etc
    text = re.sub(r'\b([A-Z])(\d)\b(?!\d)', r'$\1_{\2}$', text)

    # Pattern for equations: A = something
    text = re.sub(r'\b([A-Z])\s*=\s*', r'$\1 = $', text)

    # Clean up consecutive $ symbols
    text = re.sub(r'\$\s*\$', '', text)

    # If we made changes, mark as safe HTML
    if text != original_text:
        return mark_safe(text)

    return text

