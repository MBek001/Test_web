import os
import json
import re
from typing import List, Dict
import docx
import PyPDF2
import pdfplumber
from openai import OpenAI


class AIQuestionParser:
    """AI-powered question parser using OpenAI for 100% accuracy"""

    def __init__(self):
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)

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
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

    def parse_with_ai(self, file_path: str, answer_marking: str = None, answer_file_path: str = None) -> List[Dict]:
        """
        Parse questions using OpenAI for 100% accuracy
        Returns list of questions with options and correct answers
        """
        # Extract text from files
        question_text = self.extract_text_from_file(file_path)

        answer_text = ""
        if answer_file_path:
            answer_text = self.extract_text_from_file(answer_file_path)

        # Use AI to parse questions
        if self.client:
            return self._parse_with_openai(question_text, answer_text, answer_marking)
        else:
            # Fallback to regex parsing
            return self._parse_with_regex(question_text, answer_text, answer_marking)

    def _parse_with_openai(self, question_text: str, answer_text: str, answer_marking: str) -> List[Dict]:
        """Use OpenAI GPT-4 to parse questions perfectly"""

        # Build prompt based on answer marking type
        if answer_text:
            prompt = f"""You are a precise question parser. Extract ALL questions and answers from the text below.

QUESTION TEXT:
{question_text}

ANSWER KEY (format like: 1. B, 2. C, 3. D, etc.):
{answer_text}

CRITICAL INSTRUCTIONS:
1. Extract EVERY SINGLE question (all 100 questions if there are 100)
2. For each question, extract ALL options (A, B, C, D, etc.)
3. Match the answer key to mark which option is correct
4. Question number in answer key corresponds to question order
5. Ensure question text is COMPLETE - don't cut off
6. Ensure ALL options are included
7. Return ONLY valid JSON, no markdown formatting

Example: If answer key says "1. B", then for question 1, option B should have "is_correct": true

Return JSON in this EXACT format (must be valid JSON):
{{
  "questions": [
    {{
      "order": 1,
      "text": "Complete question text?",
      "options": [
        {{"text": "Option A", "is_correct": false, "order": 0}},
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

CRITICAL INSTRUCTIONS:
1. Extract EVERY SINGLE question - don't skip any
2. Extract ALL options for each question (A, B, C, D, etc.)
3. Identify correct answers by the markers (# at start or + at end)
4. Ensure question text is COMPLETE
5. Ensure ALL options are included
6. Remove markers (# or +) from the option text
7. Return ONLY valid JSON, no markdown formatting

Return JSON in this EXACT format (must be valid JSON):
{{
  "questions": [
    {{
      "order": 1,
      "text": "Complete question text?",
      "options": [
        {{"text": "Option A", "is_correct": false, "order": 0}},
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
        question_pattern = r'(\d+)[\.\)]\s*(.+?)(?=\d+[\.\)]|$)'

        for match in re.finditer(question_pattern, text, re.DOTALL):
            question_num = int(match.group(1))
            question_block = match.group(2).strip()

            lines = question_block.split('\n')
            question_text = lines[0].strip()

            option_pattern = r'([A-Z])[\.\)]\s*(.+?)(?=[A-Z][\.\)]|$)'
            options = []

            for opt_match in re.finditer(option_pattern, question_block, re.DOTALL):
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
