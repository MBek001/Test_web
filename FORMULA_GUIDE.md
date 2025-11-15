# Formula Support Guide

## Overview
This platform now supports mathematical formulas in tests using **MathJax**.

## How Formulas Work

### 1. **Uploading Files with Formulas**

When you upload DOCX or PDF files containing mathematical formulas:
- The system extracts equations from Word equation editor
- Formulas are preserved and marked as `[FORMULA]` in extracted text
- AI parser keeps all mathematical content

### 2. **Formula Rendering**

Formulas are rendered using MathJax. You can use:

**Inline Math** (within text):
- Use `$formula$` for inline formulas
- Example: `$A = \\pi r^2$` renders as inline formula

**Display Math** (centered, separate line):
- Use `$$formula$$` for display formulas
- Example: `$$A = \\begin{bmatrix} 2 & 4 & 1 \\\\ -1 & 3 & -2 \\\\ 3 & 2 & 3 \\end{bmatrix}$$`

### 3. **LaTeX Syntax Examples**

**Matrices:**
```latex
$$A = \\begin{bmatrix}
2 & 4 & 1 \\\\
-1 & 3 & -2 \\\\
3 & 2 & 3
\\end{bmatrix}$$
```

**Fractions:**
```latex
$\\frac{a}{b}$ or $\\frac{numerator}{denominator}$
```

**Equations:**
```latex
$ax^2 + bx + c = 0$
```

**Square Roots:**
```latex
$\\sqrt{x}$ or $\\sqrt[3]{x}$
```

**Integrals:**
```latex
$\\int_{a}^{b} f(x) dx$
```

**Summations:**
```latex
$\\sum_{i=1}^{n} x_i$
```

## AI Parsing with Formulas

The AI parser has been enhanced to:
1. **Preserve all mathematical content** from uploaded files
2. **Keep formula markers** like [FORMULA] in the text
3. **Not skip questions** that contain formulas
4. **Extract matrix notation**, equations, and mathematical symbols

## Best Practices

### For Test Creators:

1. **Use Word Equation Editor** for best results when creating DOCX files
2. **Keep formulas simple** in PDF files (extraction from PDF is limited)
3. **Manual LaTeX entry**: After uploading, you can manually edit questions to add proper LaTeX

### For Manual Formula Entry:

If formulas don't extract properly, you can:
1. Upload the test
2. Edit questions in the admin panel
3. Replace `[FORMULA]` markers with proper LaTeX syntax
4. Use the examples above as reference

## Example Question with Formula

**Question Text:**
```
Agar matritsa $A = \\begin{bmatrix} 2 & 4 \\\\ 1 & 3 \\end{bmatrix}$ bo'lsa, $\\det(A)$ ni toping?
```

**Options:**
- A) $2$
- B) $5$  ← (correct)
- C) $6$
- D) $10$

## Troubleshooting

**Problem:** Formulas appear as garbled text
**Solution:**
- Formulas were likely lost during extraction
- Manually edit the question and add LaTeX syntax
- Use the admin panel to edit questions

**Problem:** Formulas don't render
**Solution:**
- Check that formulas are wrapped in `$...$` or `$$...$$`
- Verify LaTeX syntax is correct
- MathJax may take a moment to render on page load

## Technical Details

- **MathJax Version:** 3.x (loaded from CDN)
- **Supported Formats:** LaTeX, MathML
- **Inline delimiters:** `$...$` or `\\(...\\)`
- **Display delimiters:** `$$...$$` or `\\[...\\]`
