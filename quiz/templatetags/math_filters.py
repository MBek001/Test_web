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

    # First, handle matrix patterns (must come before subscript conversion)
    # Pattern: Letter optionally followed by digits, then =, then 6+ digits/minuses
    # Removed word boundary to handle cases like A23A=...
    matrix_pattern = r'([A-Z]\d*)\s*=\s*([0-9\-]{6,})(?=\s|$|[^0-9\-])'

    def convert_to_matrix(match):
        var_name = match.group(1)
        numbers_str = match.group(2)

        # Parse concatenated numbers (assuming single digits with optional minus)
        numbers = []
        i = 0
        while i < len(numbers_str):
            if numbers_str[i] == '-':
                if i + 1 < len(numbers_str):
                    numbers.append(-int(numbers_str[i + 1]))
                    i += 2
                else:
                    i += 1
            else:
                numbers.append(int(numbers_str[i]))
                i += 1

        # Determine matrix dimensions (try to make it square)
        n = len(numbers)
        if n == 4:
            rows, cols = 2, 2
        elif n == 9:
            rows, cols = 3, 3
        elif n == 16:
            rows, cols = 4, 4
        elif n == 6:
            rows, cols = 2, 3
        elif n == 8:
            rows, cols = 2, 4
        elif n == 12:
            rows, cols = 3, 4
        else:
            # Default to trying square root
            import math
            sqrt_n = int(math.sqrt(n))
            if sqrt_n * sqrt_n == n:
                rows, cols = sqrt_n, sqrt_n
            else:
                # Can't determine, return original
                return match.group(0)

        # Build matrix
        matrix_rows = []
        for i in range(rows):
            row = []
            for j in range(cols):
                idx = i * cols + j
                if idx < len(numbers):
                    row.append(str(numbers[idx]))
            matrix_rows.append(' & '.join(row))

        matrix_content = ' \\\\ '.join(matrix_rows)
        return f"${var_name} = \\begin{{bmatrix}} {matrix_content} \\end{{bmatrix}}$"

    text = re.sub(matrix_pattern, convert_to_matrix, text)

    # Pattern for matrix variables with subscripts: A32, A23, etc
    # Only convert if not already part of a matrix pattern (not followed by =)
    text = re.sub(r'(?<!\$)([A-Z])(\d{2})(?!\s*=)', r'$\1_{\2}$', text)

    # Pattern for simple variable subscripts: A1, A2, etc
    text = re.sub(r'(?<!\$)([A-Z])(\d)(?!\d)(?!\s*=)', r'$\1_{\2}$', text)

    # Clean up consecutive $ symbols and whitespace issues
    text = re.sub(r'\$\s*\$', ' ', text)
    text = re.sub(r'\$\s*\$', ' ', text)  # Run twice to catch any remaining
    text = text.replace('$ $', ' ')

    # If we made changes, mark as safe HTML
    if text != original_text:
        return mark_safe(text)

    return text

