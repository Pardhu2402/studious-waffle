from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import re
import os

# Register multilingual fonts
def register_multilingual_fonts():
    """Register static TTF fonts for Hindi, Telugu, and Kannada scripts (not variable)"""
    font_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
    try:
        pdfmetrics.registerFont(TTFont('NotoSansDevanagari-Regular', os.path.join(font_dir, 'NotoSansDevanagari-Regular.ttf')))
    except Exception as e:
        print(f"Warning: Could not register Devanagari regular font: {e}")
    try:
        pdfmetrics.registerFont(TTFont('NotoSansTelugu-Regular', os.path.join(font_dir, 'NotoSansTelugu-Regular.ttf')))
    except Exception as e:
        print(f"Warning: Could not register Telugu regular font: {e}")
    try:
        pdfmetrics.registerFont(TTFont('NotoSansKannada-Regular', os.path.join(font_dir, 'NotoSansKannada-Regular.ttf')))
    except Exception as e:
        print(f"Warning: Could not register Kannada regular font: {e}")

# Register fonts on module import
register_multilingual_fonts()

def get_noto_font_for_language(language, is_bold=False):
    """Return the Noto static font name for the given language, always use Noto for that language (even for English words)."""
    if language == 'hindi':
        return 'NotoSansDevanagari-Regular'
    elif language == 'telugu':
        return 'NotoSansTelugu-Regular'
    elif language == 'kannada':
        return 'NotoSansKannada-Regular'
    else:
        return 'Helvetica-Bold' if is_bold else 'Helvetica'

class AIContentPDFGenerator:
    def __init__(self, language='english'):
        self.language = language
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def get_font_for_language(self, is_bold=False):
        return get_noto_font_for_language(self.language, is_bold)
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for better formatting with multilingual support"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName=self.get_font_for_language(is_bold=True),
            wordWrap='CJK'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=20,
            textColor=colors.darkblue,
            fontName=self.get_font_for_language(is_bold=True),
            wordWrap='CJK'
        )
        
        # Section header style
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=16,
            textColor=colors.darkgreen,
            fontName=self.get_font_for_language(is_bold=True),
            wordWrap='CJK'
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName=self.get_font_for_language(is_bold=False),
            wordWrap='CJK'
        )
        
        # Bullet point style
        self.bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            fontName=self.get_font_for_language(is_bold=False),
            wordWrap='CJK'
        )
    
    def generate_summary_pdf(self, content, title="AI Generated Summary"):
        """Generate PDF for summary content"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        story = []
        
        # Title
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Process content
        story.extend(self.process_content_for_pdf(content))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_quiz_pdf(self, content, title="AI Generated Quiz"):
        """Generate PDF for quiz content"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        story = []
        
        # Title
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Instructions
        story.append(Paragraph("Instructions:", self.subtitle_style))
        story.append(Paragraph("• Read each question carefully", self.bullet_style))
        story.append(Paragraph("• Choose the best answer from the options provided", self.bullet_style))
        story.append(Paragraph("• Write your answers in the space provided", self.bullet_style))
        story.append(Spacer(1, 20))
        
        # Process content
        story.extend(self.process_content_for_pdf(content))
        
        # Add answer key section
        story.append(PageBreak())
        story.append(Paragraph("Answer Key", self.subtitle_style))
        story.append(Paragraph("Answers will be provided by your teacher.", self.body_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_worksheet_pdf(self, content, title="AI Generated Worksheet"):
        """Generate PDF for worksheet content"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        story = []
        
        # Title
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Instructions
        story.append(Paragraph("Worksheet Instructions:", self.subtitle_style))
        story.append(Paragraph("• Complete all activities in this worksheet", self.bullet_style))
        story.append(Paragraph("• Show your work and reasoning", self.bullet_style))
        story.append(Paragraph("• Use the space provided for your answers", self.bullet_style))
        story.append(Spacer(1, 20))
        
        # Process content
        story.extend(self.process_content_for_pdf(content))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_mcq_pdf(self, content, title="AI Generated MCQ Questions"):
        """Generate PDF for MCQ content"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        story = []
        
        # Title
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Instructions
        story.append(Paragraph("Multiple Choice Questions:", self.subtitle_style))
        story.append(Paragraph("• Choose the correct answer from the options (A, B, C, D)", self.bullet_style))
        story.append(Paragraph("• Circle or mark your answer clearly", self.bullet_style))
        story.append(Paragraph("• Only one answer is correct for each question", self.bullet_style))
        story.append(Spacer(1, 20))
        
        # Process content
        story.extend(self.process_content_for_pdf(content))
        
        # Add answer key section
        story.append(PageBreak())
        story.append(Paragraph("Answer Key", self.subtitle_style))
        story.append(Paragraph("Answers will be provided by your teacher.", self.body_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def process_content_for_pdf(self, content):
        """Process content and convert to PDF elements"""
        story = []
        
        # Split content into sections
        sections = content.split('\n\n')
        
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            first_line = lines[0].strip()
            
            # Check if it's a header
            if first_line.startswith('#'):
                # Remove # symbols and create header
                header_text = first_line.lstrip('#').strip()
                if first_line.startswith('###'):
                    story.append(Paragraph(header_text, self.section_style))
                elif first_line.startswith('##'):
                    story.append(Paragraph(header_text, self.subtitle_style))
                else:
                    story.append(Paragraph(header_text, self.title_style))
                
                # Process remaining lines in this section
                remaining_lines = lines[1:]
                if remaining_lines:
                    story.extend(self.process_text_lines(remaining_lines))
            else:
                # Regular text section
                story.extend(self.process_text_lines(lines))
            
            story.append(Spacer(1, 12))
        
        return story
    
    def process_text_lines(self, lines):
        """Process text lines and convert to appropriate PDF elements"""
        story = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for bullet points
            if line.startswith('* ') or line.startswith('- '):
                # Remove bullet marker and create bullet point
                text = line[2:].strip()
                story.append(Paragraph(f"• {text}", self.bullet_style))
            elif line.startswith('**') and line.endswith('**'):
                # Bold text
                text = line[2:-2].strip()
                story.append(Paragraph(f"<b>{text}</b>", self.body_style))
            elif line.startswith('*') and line.endswith('*'):
                # Italic text
                text = line[1:-1].strip()
                story.append(Paragraph(f"<i>{text}</i>", self.body_style))
            else:
                # Regular text
                story.append(Paragraph(line, self.body_style))
        
        return story

def generate_ai_content_pdf(content, action_type, item_name, language='english'):
    """Main function to generate PDF based on action type with language support"""
    generator = AIContentPDFGenerator(language)
    
    if action_type == 'summarize':
        return generator.generate_summary_pdf(content, f"Summary: {item_name}")
    elif action_type == 'quiz':
        return generator.generate_quiz_pdf(content, f"Quiz: {item_name}")
    elif action_type == 'worksheet':
        return generator.generate_worksheet_pdf(content, f"Worksheet: {item_name}")
    elif action_type == 'mcq':
        return generator.generate_mcq_pdf(content, f"MCQ Questions: {item_name}")
    else:
        # Default to summary format
        return generator.generate_summary_pdf(content, f"{action_type.title()}: {item_name}")

def create_worksheet_pdf(worksheet_content, grade, language='english', filename="worksheet.pdf"):
    """Create a beautiful PDF worksheet from the AI-generated content with multilingual support"""
    
    # Create a buffer to store the PDF
    buffer = BytesIO()
    
    # Create the PDF document
    # Reduce margins for more space
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Get font for language
    def get_font(is_bold=False):
        return get_noto_font_for_language(language, is_bold)
    
    # Helper to get font size based on language
    def get_font_size(language, default_size):
        if language in ['hindi', 'telugu', 'kannada']:
            return max(default_size - 1, 9)  # Slightly smaller for Indian scripts
        return default_size

    # Create custom styles with language-specific fonts and wordWrap
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=get_font_size(language, 24),
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName=get_font(is_bold=True),
        wordWrap='CJK'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=get_font_size(language, 16),
        spaceAfter=20,
        spaceBefore=20,
        textColor=colors.darkgreen,
        fontName=get_font(is_bold=True),
        wordWrap='CJK'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=get_font_size(language, 12),
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName=get_font(is_bold=False),
        wordWrap='CJK'
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=get_font_size(language, 12),
        spaceAfter=8,
        spaceBefore=8,
        leftIndent=20,
        fontName=get_font(is_bold=True),
        textColor=colors.darkblue,
        wordWrap='CJK'
    )
    
    instruction_style = ParagraphStyle(
        'Instruction',
        parent=styles['Normal'],
        fontSize=get_font_size(language, 11),
        spaceAfter=10,
        spaceBefore=10,
        fontName=get_font(is_bold=False),
        textColor=colors.darkgreen,
        wordWrap='CJK'
    )
    
    # Build the PDF content
    story = []
    
    # Header
    story.append(Paragraph("🧠 Sahayak+ AI Teaching Assistant", title_style))
    story.append(Spacer(1, 20))
    
    # Grade and date info
    grade_info = f"<b>Grade Level:</b> {grade} | <b>Generated by:</b> Gemini AI"
    story.append(Paragraph(grade_info, body_style))
    story.append(Spacer(1, 30))
    
    # Process the worksheet content
    sections = parse_worksheet_content(worksheet_content, language)
    
    for section in sections:
        if section['type'] == 'title':
            story.append(Paragraph(section['content'], title_style))
        elif section['type'] == 'subtitle':
            story.append(Paragraph(section['content'], subtitle_style))
        elif section['type'] == 'question':
            story.append(Paragraph(section['content'], question_style))
        elif section['type'] == 'instruction':
            story.append(Paragraph(section['content'], instruction_style))
        elif section['type'] == 'text':
            story.append(Paragraph(section['content'], body_style))
        elif section['type'] == 'list':
            for item in section['content']:
                story.append(Paragraph(f"• {item}", body_style))
        elif section['type'] == 'table':
            story.append(section['content'])
        
        story.append(Spacer(1, 12))
    
    # Add footer
    story.append(Spacer(1, 30))
    footer_text = "Generated by Sahayak+ AI Teaching Assistant | Powered by Google Gemini AI"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontName=get_font(is_bold=False)
    )))
    
    # Build the PDF
    doc.build(story)
    
    # Get the PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def parse_worksheet_content(content, language='english'):
    """Parse the worksheet content into structured sections with language support"""
    sections = []
    
    # Split content into lines
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # Detect title (usually in ** or all caps)
        if line.startswith('**') and line.endswith('**'):
            sections.append({
                'type': 'title',
                'content': line.strip('*')
            })
        # Detect subtitles (usually start with Section, Part, etc.)
        elif re.match(r'^(Section|Part|Chapter|Activity|Exercise)\s+\d+', line, re.IGNORECASE):
            sections.append({
                'type': 'subtitle',
                'content': line
            })
        # Detect questions (usually start with numbers)
        elif re.match(r'^\d+\.', line):
            sections.append({
                'type': 'question',
                'content': line
            })
        # Detect instructions (Look closely, Answer the following, etc.)
        elif re.match(r'^(Look|Answer|Choose|Write|Design|Imagine|Complete)', line, re.IGNORECASE):
            sections.append({
                'type': 'instruction',
                'content': line
            })
        # Detect tables
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_data = []
            # Collect table rows
            while i < len(lines) and '|' in lines[i]:
                row = [cell.strip() for cell in lines[i].split('|') if cell.strip()]
                if row:
                    table_data.append(row)
                i += 1
            
            if table_data:
                # Create ReportLab table with language-specific font
                table = Table(table_data)
                font_name = 'Helvetica-Bold'
                if language == 'hindi':
                    font_name = 'NotoSansDevanagari-Bold'
                elif language == 'telugu':
                    font_name = 'NotoSansTelugu-Bold'
                elif language == 'kannada':
                    font_name = 'NotoSansKannada-Bold'
                
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                sections.append({
                    'type': 'table',
                    'content': table
                })
            continue
        # Detect bullet points
        elif line.startswith('*') or line.startswith('-'):
            sections.append({
                'type': 'list',
                'content': [line.lstrip('*- ')]
            })
        # Regular text
        else:
            sections.append({
                'type': 'text',
                'content': line
            })
        
        i += 1
    
    return sections

def create_simple_pdf(worksheet_content, grade, language='english'):
    """Create a simple formatted PDF for the worksheet with language support"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Get font for language
    def get_font(is_bold=False):
        if language == 'hindi':
            return 'NotoSansDevanagari-Bold' if is_bold else 'NotoSansDevanagari-Regular'
        elif language == 'telugu':
            return 'NotoSansTelugu-Bold' if is_bold else 'NotoSansTelugu-Regular'
        elif language == 'kannada':
            return 'NotoSansKannada-Bold' if is_bold else 'NotoSansKannada-Regular'
        else:
            return 'Helvetica-Bold' if is_bold else 'Helvetica'
    
    # Helper to get font size based on language
    def get_font_size(language, default_size):
        if language in ['hindi', 'telugu', 'kannada']:
            return max(default_size - 1, 9)  # Slightly smaller for Indian scripts
        return default_size

    # Create language-specific styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=get_font_size(language, 24),
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName=get_font(is_bold=True),
        wordWrap='CJK'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=get_font_size(language, 12),
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName=get_font(is_bold=False),
        wordWrap='CJK'
    )
    
    # Title
    story.append(Paragraph("🧠 Sahayak+ AI Worksheet", title_style))
    story.append(Spacer(1, 20))
    
    # Grade info
    story.append(Paragraph(f"<b>Grade:</b> {grade}", body_style))
    story.append(Spacer(1, 30))
    
    # Content
    paragraphs = worksheet_content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para, body_style))
            story.append(Spacer(1, 12))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Generated by Sahayak+ AI Teaching Assistant", body_style))
    
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content 