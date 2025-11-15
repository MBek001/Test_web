import os
import json
import re
from typing import List, Dict
import docx
import PyPDF2
import pdfplumber
from openai import OpenAI


class AIQuestionParser:
    """AI-powered question parser using OpenAI"""

    def __init__(self):
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)

    def convert_office_math_to_latex(self, text: str) -> str:
        """Convert Office Math ML to LaTeX"""

        def convert_matrix(match):
            matrix_content = match.group(1)
            rows = matrix_content.split('##')
            latex_rows = []
            for row in rows:
                cols = row.strip().split('#')
                cols = [c.strip().replace('"', '') for c in cols]
                latex_rows.append(' & '.join(cols))
            matrix_latex = ' \\\\ '.join(latex_rows)

            if 'left (' in match.group(0) or 'left(' in match.group(0):
                return f"$\\begin{{pmatrix}} {matrix_latex} \\end{{pmatrix}}$"
            elif 'left [' in match.group(0) or 'left[' in match.group(0):
                return f"$\\begin{{bmatrix}} {matrix_latex} \\end{{bmatrix}}$"
            else:
                return f"$\\begin{{matrix}} {matrix_latex} \\end{{matrix}}$"

        text = re.sub(r'left\s*[\(\[]?\s*matrix\s*\{([^}]+)\}\s*right\s*[\)\]]?', convert_matrix, text, flags=re.IGNORECASE)
        text = re.sub(r'matrix\s*\{([^}]+)\}', convert_matrix, text, flags=re.IGNORECASE)

        return text

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract raw text from PDF or DOCX"""
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.pdf']:
            return self._extract_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return self._extract_from_docx(file_path)
        return ""

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        except:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
        return text

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX including equations/formulas"""
        doc = docx.Document(file_path)
        full_text = []

        for paragraph in doc.paragraphs:
            para_text = paragraph.text

            for run in paragraph.runs:
                if run.element.xml:
                    if 'w:drawing' in run.element.xml or 'm:oMath' in run.element.xml:
                        equation_text = self._extract_equation_from_run(run)
                        if equation_text and equation_text not in para_text:
                            para_text += f" {equation_text} "

            para_xml = paragraph._element.xml.decode('utf-8') if isinstance(paragraph._element.xml, bytes) else str(paragraph._element.xml)
            if 'm:oMath' in para_xml or 'm:oMathPara' in para_xml:
                equation_markers = self._extract_equations_from_paragraph(paragraph)
                for eq in equation_markers:
                    if eq not in para_text:
                        para_text += f" {eq} "

            full_text.append(para_text)

        return '\n'.join(full_text)

    def _extract_equation_from_run(self, run) -> str:
        """Extract equation text from run"""
        try:
            xml_str = run.element.xml.decode('utf-8') if isinstance(run.element.xml, bytes) else str(run.element.xml)

            if 'm:t' in xml_str:
                import re
                matches = re.findall(r'<m:t>([^<]+)</m:t>', xml_str)
                if matches:
                    return ''.join(matches)

            if 'm:oMath' in xml_str:
                return "[FORMULA]"

        except:
            pass
        return ""

    def _extract_equations_from_paragraph(self, paragraph) -> list:
        """Extract equations from paragraph"""
        equations = []
        try:
            xml_str = paragraph._element.xml.decode('utf-8') if isinstance(paragraph._element.xml, bytes) else str(paragraph._element.xml)

            import re
            math_texts = re.findall(r'<m:t>([^<]+)</m:t>', xml_str)
            if math_texts:
                equations.append(''.join(math_texts))
            elif 'm:oMath' in xml_str:
                equations.append("[FORMULA]")

        except:
            pass
        return equations

    def parse_with_ai(self, file_path: str, answer_marking: str = None, answer_file_path: str = None) -> List[Dict]:
        """Parse questions using OpenAI"""
        question_text = self.extract_text_from_file(file_path)

        answer_text = ""
        if answer_file_path:
            answer_text = self.extract_text_from_file(answer_file_path)

        if self.client:
            return self._parse_with_openai(question_text, answer_text, answer_marking)
        else:
            return self._parse_with_regex(question_text, answer_text, answer_marking)

    def _parse_with_openai(self, question_text: str, answer_text: str, answer_marking: str) -> List[Dict]:
        """Use OpenAI to parse questions"""

        question_text = self.convert_office_math_to_latex(question_text)
        if answer_text:
            answer_text = self.convert_office_math_to_latex(answer_text)

        if answer_text:
            prompt = f"""You are a precise question parser. Extract ALL questions and answers from the text below.

QUESTION TEXT:
{question_text}

ANSWER KEY (format like: 1. B, 2. C, 3. D, etc.):
{answer_text}

CRITICAL FORMAT UNDERSTANDING:
- Questions are numbered: "1. Question text here?" or "1) Question text here?"
- Options are lettered: "A) Option text", "B) Option text", "C) Option text", "D) Option text"
- DO NOT confuse option letters (A, B, C, D) with question numbers
- Each question has 4 options (A, B, C, D) - extract ALL of them

CRITICAL INSTRUCTIONS:
1. Extract EVERY SINGLE question (all 100 questions if there are 100)
2. For each question, extract the FULL question text (everything after "1." until the first option "A)")
3. Extract ALL 4 options (A, B, C, D) for each question
4. Match the answer key to mark which option is correct
5. Question number in answer key corresponds to question order
6. Ensure question text is COMPLETE - include everything between question number and first option
7. Remove the letter prefix (A), B), C), D)) from option text
8. PRESERVE [FORMULA] markers and mathematical expressions EXACTLY
9. Return ONLY valid JSON, no markdown formatting

IMPORTANT: Mathematical formulas may appear as [FORMULA] or as text like "matrix", "A=", numbers, etc.
Keep ALL mathematical content in the question and option text.

FORMULA HANDLING - VERY IMPORTANT:
- Convert Office Math ML format to LaTeX (e.g., "left (matrix {{...}} right )" → "$\\begin{{bmatrix}}...$")
- Matrix format: "matrix {{2 # 4 # 1 ## -1 # 3 # -2}}" → "$\\begin{{bmatrix}} 2 & 4 & 1 \\\\ -1 & 3 & -2 \\end{{bmatrix}}$"
- In matrices, "#" separates columns, "##" separates rows
- "left (" and "right )" indicate parentheses around matrices
- Simple equations: wrap in $ symbols (e.g., "x^2" → "$x^2$", "A=" → "$A=$")
- Fractions: "frac{{a}}{{b}}" → "$\\frac{{a}}{{b}}$"
- Square roots: "sqrt{{x}}" → "$\\sqrt{{x}}$"
- Subscripts/superscripts: "x_1", "x^2" → "$x_1$", "$x^2$"
- Keep [FORMULA] only if formula cannot be interpreted

Example: If answer key says "1. B", then for question 1, option B should have "is_correct": true

Return JSON in this EXACT format (must be valid JSON):
{{
  "questions": [
    {{
      "order": 1,
      "text": "Complete question text with formulas?",
      "options": [
        {{"text": "Option A with [FORMULA] if present", "is_correct": false, "order": 0}},
        {{"text": "Option B", "is_correct": true, "order": 1}},
        {{"text": "Option C", "is_correct": false, "order": 2}},
        {{"text": "Option D", "is_correct": false, "order": 3}}
      ]
    }}
  ]
}}

Extract ALL questions now:"""
        else:
            # Questions and answers in same file
            marker_info = ""
            if answer_marking == 'hash_start':
                marker_info = "Correct answers are marked with # at the start"
            elif answer_marking == 'plus_end':
                marker_info = "Correct answers are marked with + or ++++ at the end"

            prompt = f"""You are a precise question parser. Extract ALL questions and answers from the text below.

TEXT:
{question_text}

ANSWER MARKING: {marker_info}

CRITICAL FORMAT UNDERSTANDING:
- Questions are numbered: "1. Question text here?" or "1) Question text here?"
- Options are lettered: "A) Option text", "B) Option text", "C) Option text", "D) Option text"
- DO NOT confuse option letters (A, B, C, D) with question numbers
- Each question has 4 options - extract ALL of them

CRITICAL INSTRUCTIONS:
1. Extract EVERY SINGLE question - don't skip any
2. For each question, extract the FULL question text (everything after "1." until the first option "A)")
3. Extract ALL 4 options (A, B, C, D) for each question
4. Identify correct answers by the markers (# at start or + at end)
5. Ensure question text is COMPLETE - include everything between question number and first option
6. Remove the letter prefix (A), B), C), D)) and markers (# or +) from option text
7. PRESERVE [FORMULA] markers and mathematical expressions EXACTLY
8. Return ONLY valid JSON, no markdown formatting

IMPORTANT: Mathematical formulas may appear as [FORMULA] or as text like "matrix", "A=", numbers, etc.
Keep ALL mathematical content in the question and option text.

FORMULA HANDLING - VERY IMPORTANT:
- Convert Office Math ML format to LaTeX (e.g., "left (matrix {{...}} right )" → "$\\begin{{bmatrix}}...$")
- Matrix format: "matrix {{2 # 4 # 1 ## -1 # 3 # -2}}" → "$\\begin{{bmatrix}} 2 & 4 & 1 \\\\ -1 & 3 & -2 \\end{{bmatrix}}$"
- In matrices, "#" separates columns, "##" separates rows
- "left (" and "right )" indicate parentheses around matrices
- Simple equations: wrap in $ symbols (e.g., "x^2" → "$x^2$", "A=" → "$A=$")
- Fractions: "frac{{a}}{{b}}" → "$\\frac{{a}}{{b}}$"
- Square roots: "sqrt{{x}}" → "$\\sqrt{{x}}$"
- Subscripts/superscripts: "x_1", "x^2" → "$x_1$", "$x^2$"
- Keep [FORMULA] only if formula cannot be interpreted

Return JSON in this EXACT format (must be valid JSON):
{{
  "questions": [
    {{
      "order": 1,
      "text": "Complete question text with formulas?",
      "options": [
        {{"text": "Option A with [FORMULA] if present", "is_correct": false, "order": 0}},
        {{"text": "Option B", "is_correct": true, "order": 1}},
        {{"text": "Option C", "is_correct": false, "order": 2}},
        {{"text": "Option D", "is_correct": false, "order": 3}}
      ]
    }}
  ]
}}

Extract ALL questions now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # or gpt-4 for best accuracy
                messages=[
                    {"role": "system", "content": "You are a precise question parser. Extract questions exactly as they appear, ensuring completeness."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content
            parsed = json.loads(result)

            # Handle both array and object with questions key
            if isinstance(parsed, dict) and 'questions' in parsed:
                return parsed['questions']
            elif isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and len(parsed) > 0:
                # Try to find questions array in the dict
                for key in parsed:
                    if isinstance(parsed[key], list):
                        return parsed[key]

            return []

        except Exception as e:
            print(f"OpenAI parsing error: {str(e)}")
            # Fallback to regex
            return self._parse_with_regex(question_text, answer_text, answer_marking)

    def _parse_with_regex(self, question_text: str, answer_text: str, answer_marking: str) -> List[Dict]:
        """Fallback regex-based parsing"""
        questions = []

        if answer_text:
            # Parse separate answer file
            questions = self._parse_questions_only(question_text)
            answers = self._parse_answers(answer_text)
            questions = self._merge_answers(questions, answers)
        elif answer_marking == 'hash_start':
            questions = self._parse_hash_format(question_text)
        elif answer_marking == 'plus_end':
            questions = self._parse_plus_format(question_text)

        return questions

    def _parse_hash_format(self, text: str) -> List[Dict]:
        """Parse # format"""
        questions = []
        blocks = text.split('++++')

        for idx, block in enumerate(blocks):
            block = block.strip()
            if not block:
                continue

            parts = [p.strip() for p in block.split('====') if p.strip()]
            if len(parts) < 2:
                continue

            question_text = parts[0]
            options = []

            for i, option_text in enumerate(parts[1:]):
                is_correct = option_text.startswith('#')
                clean_text = option_text.lstrip('#').strip()

                if clean_text:  # Only add non-empty options
                    options.append({
                        'text': clean_text,
                        'is_correct': is_correct,
                        'order': i
                    })

            if options:
                questions.append({
                    'text': question_text,
                    'options': options,
                    'order': idx + 1
                })

        return questions

    def _parse_plus_format(self, text: str) -> List[Dict]:
        """Parse ++++ format"""
        questions = []
        question_pattern = r'(\d+)[\.\)]\s*(.+?)(?=\d+[\.\)]|$)'

        for match in re.finditer(question_pattern, text, re.DOTALL):
            question_num = int(match.group(1))
            question_block = match.group(2).strip()

            lines = question_block.split('\n')
            question_text = lines[0].strip()

            option_pattern = r'([A-Z])[\.\)]\s*(.+?)(?=[A-Z][\.\)]|$)'
            options = []

            for opt_match in re.finditer(option_pattern, question_block, re.DOTALL):
                option_text = opt_match.group(2).strip()
                is_correct = '+++' in option_text
                clean_text = option_text.replace('++++', '').replace('+++', '').strip()
                clean_text = clean_text.lstrip('○').strip()

                if clean_text:
                    options.append({
                        'text': clean_text,
                        'is_correct': is_correct,
                        'order': len(options)
                    })

            if options and question_text:
                questions.append({
                    'text': question_text,
                    'options': options,
                    'order': question_num
                })

        return questions

    def _parse_questions_only(self, text: str) -> List[Dict]:
        """Parse questions without answers"""
        questions = []
        question_pattern = r'^\s*(\d+)[\.\)]\s+(.+?)(?=^\s*\d+[\.\)]|\Z)'

        for match in re.finditer(question_pattern, text, re.DOTALL | re.MULTILINE):
            question_num = int(match.group(1))
            question_block = match.group(2).strip()

            option_pattern = r'^([A-Z])\)\s*(.+?)(?=^[A-Z]\)|\Z)'
            option_matches = list(re.finditer(option_pattern, question_block, re.DOTALL | re.MULTILINE))

            if option_matches:
                question_text = question_block[:question_block.find(option_matches[0].group(0))].strip()
            else:
                question_text = question_block.strip()

            options = []
            for opt_match in option_matches:
                letter = opt_match.group(1)
                option_text = opt_match.group(2).strip().lstrip('○').strip()

                if option_text:
                    options.append({
                        'text': option_text,
                        'is_correct': False,
                        'order': len(options),
                        'letter': letter
                    })

            if options and question_text:
                questions.append({
                    'text': question_text,
                    'options': options,
                    'order': question_num
                })

        return questions

    def _parse_answers(self, answer_text: str) -> Dict[int, str]:
        """Parse answer file"""
        answers = {}
        pattern = r'(\d+)[\.\)]\s*([A-Z])'

        for match in re.finditer(pattern, answer_text):
            question_num = int(match.group(1))
            answer_letter = match.group(2)
            answers[question_num] = answer_letter

        return answers

    def _merge_answers(self, questions: List[Dict], answers: Dict[int, str]) -> List[Dict]:
        """Merge answers with questions"""
        for question in questions:
            question_num = question['order']
            if question_num in answers:
                correct_letter = answers[question_num]
                for option in question['options']:
                    if option.get('letter') == correct_letter:
                        option['is_correct'] = True

        return questions
