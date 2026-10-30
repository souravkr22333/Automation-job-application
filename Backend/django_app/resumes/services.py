# backend/django_app/resumes/services.py
import os
import re
import uuid
import PyPDF2
import docx
import logging
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

# Try to import from core, fallback to local
from core.supabase_client import supabase_client


logger = logging.getLogger(__name__)


def build_tailored_resume_name(resume_name: str, company_name: str) -> str:
    """Build a descriptive resume name within the model's 255-character limit."""
    suffix = f" - Tailored for {company_name}"
    if len(suffix) >= 255:
        return suffix[-255:]
    return f"{resume_name[:255 - len(suffix)]}{suffix}"


class ResumeParser:
    """Parse resume files and extract information"""

    @staticmethod
    def parse_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to parse PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def parse_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to parse DOCX: {str(e)}")
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

    @staticmethod
    def parse_resume(file_content: bytes, content_type: str) -> str:
        """Parse resume based on file type"""
        if content_type == 'application/pdf':
            return ResumeParser.parse_pdf(file_content)
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/msword']:
            return ResumeParser.parse_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {content_type}")

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
        """Extract contact information from resume text"""
        info = {}

        # Extract email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, text)
        info['email'] = email_match.group(0) if email_match else None

        # Extract phone
        phone_patterns = [
            r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}',
            r'(\+\d{1,3}[- ]?)?\d{3}[- ]?\d{3}[- ]?\d{4}',
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                info['phone'] = phone_match.group(0)
                break

        return info

    @staticmethod
    def extract_skills(text: str, skill_list: List[str] = None) -> List[str]:
        """Extract skills from text"""
        if not skill_list:
            skill_list = [
                'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go',
                'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI',
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes',
                'AWS', 'Azure', 'GCP', 'Git', 'CI/CD', 'Agile', 'Scrum',
                'Machine Learning', 'AI', 'Data Science', 'NLP', 'Computer Vision'
            ]

        text_lower = text.lower()
        found_skills = []

        for skill in skill_list:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        return found_skills

    @staticmethod
    def extract_experience(text: str) -> int:
        """Extract years of experience"""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)',
            r'(?:years?|yrs?)\s+of\s+experience\s*(?:with)?\s*(\d+)\+?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    years = int(match.group(1))
                    if 0 < years < 50:
                        return years
                except (ValueError, IndexError):
                    continue

        return 0

    @staticmethod
    def extract_job_titles(text: str) -> List[str]:
        """Extract job titles from text"""
        common_titles = [
            'Software Engineer', 'Senior Software Engineer', 'Lead Software Engineer',
            'Full Stack Developer', 'Frontend Developer', 'Backend Developer',
            'React Developer', 'Python Developer', 'Java Developer',
            'DevOps Engineer', 'Cloud Engineer', 'Data Scientist',
            'Machine Learning Engineer', 'AI Engineer'
        ]

        titles = []
        for title in common_titles:
            if title.lower() in text.lower():
                titles.append(title)

        return titles[:5]


class ResumeStorageService:
    """Service for managing resume files in Supabase storage"""

    BUCKET_NAME = 'resumes'
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
    ]
    ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc']

    def __init__(self):
        self.client = supabase_client

    @classmethod
    def validate_file(cls, file: UploadedFile) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file"""
        if file.size > cls.MAX_FILE_SIZE:
            return False, f"File size exceeds {cls.MAX_FILE_SIZE // (1024 * 1024)}MB limit"

        if file.content_type not in cls.ALLOWED_TYPES:
            return False, f"Unsupported file type. Allowed: {', '.join(cls.ALLOWED_TYPES)}"

        ext = file.name.split('.')[-1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension. Allowed: {', '.join(cls.ALLOWED_EXTENSIONS)}"

        return True, None

    def upload_resume(self, user_id: str, file: UploadedFile) -> Dict:
        """Upload a resume to Supabase storage"""
        if not self.client:
            raise Exception("Supabase client not available. Please check your configuration.")

        is_valid, error = self.validate_file(file)
        if not is_valid:
            raise ValueError(error)

        ext = file.name.split('.')[-1].lower()
        filename = f"resume.{ext}"
        storage_path = f"users/{user_id}/{filename}"

        try:
            result = self.client.upload_file(
                bucket_name=self.BUCKET_NAME,
                file_path=storage_path,
                file_content=file.read(),
                content_type=file.content_type
            )

            return {
                'public_url': result['public_url'],
                'path': result['path'],
                'bucket': result['bucket'],
                'file_size': file.size,
                'content_type': file.content_type,
                'filename': file.name
            }
        except Exception as e:
            logger.error(f"Failed to upload resume: {str(e)}")
            raise

    def delete_resume(self, user_id: str, file_path: str) -> bool:
        """Delete a resume from Supabase storage"""
        if not self.client:
            return False

        try:
            return self.client.delete_file(self.BUCKET_NAME, file_path)
        except Exception as e:
            logger.error(f"Failed to delete resume: {str(e)}")
            return False

    def download_resume(self, file_path: str) -> bytes:
        """Download a resume from Supabase storage"""
        if not self.client:
            raise Exception("Supabase client not available")

        try:
            return self.client.download_file(self.BUCKET_NAME, file_path)
        except Exception as e:
            logger.error(f"Failed to download resume: {str(e)}")
            raise

    def get_resume_url(self, file_path: str) -> str:
        """Get the public URL of a resume"""
        if not self.client:
            return ""
        return self.client.get_file_url(self.BUCKET_NAME, file_path)

    def upload_bytes(self, bucket_name: str, user_id: str, file_bytes: bytes, filename: str, content_type: str = 'application/pdf') -> Dict:
        """
        Upload raw bytes to a Supabase bucket (for any bucket).
        Used for uploading generated PDFs to the 'tailored_resumes' bucket.

        Args:
            bucket_name: Target bucket (e.g. 'tailored_resumes')
            user_id: User ID for path organization
            file_bytes: Raw file content as bytes
            filename: Full filename (e.g. 'resume_abc123.pdf')
            content_type: MIME type

        Returns:
            dict: {'public_url': str, 'path': str, 'bucket': str, 'file_size': int, 'content_type': str, 'filename': str}
        """
        if not self.client:
            raise Exception("Supabase client not available. Please check your configuration.")

        # Every generated version gets a new object key; retries must not collide
        # with an earlier upload that used the same display filename.
        name, extension = os.path.splitext(filename)
        storage_filename = f"{name}_{uuid.uuid4().hex}{extension}"
        storage_path = f"users/{user_id}/{storage_filename}"

        try:
            result = self.client.upload_file(
                bucket_name=bucket_name,
                file_path=storage_path,
                file_content=file_bytes,
                content_type=content_type
            )

            return {
                'public_url': result['public_url'],
                'path': result['path'],
                'bucket': result['bucket'],
                'file_size': len(file_bytes),
                'content_type': content_type,
                'filename': storage_filename
            }
        except Exception as e:
            logger.error(f"Failed to upload bytes to Supabase bucket '{bucket_name}': {str(e)}")
            raise


class PDFGenerator:
    """
    Generate PDF documents from plain text (resume content).
    Uses fpdf2 library with Arial Unicode font for full character support
    (en-dashes, bullets, smart quotes, etc.).
    """

    _fonts_registered = False

    @staticmethod
    def _register_fonts(pdf):
        """Register Arial Unicode fonts for full character support.
        Falls back to Helvetica if Arial is not available on Windows."""
        if PDFGenerator._fonts_registered:
            return True

        import os
        WINDOWS_FONTS_DIR = "C:\\Windows\\Fonts"
        arial_paths = {
            '': os.path.join(WINDOWS_FONTS_DIR, 'arial.ttf'),
            'B': os.path.join(WINDOWS_FONTS_DIR, 'arialbd.ttf'),
            'I': os.path.join(WINDOWS_FONTS_DIR, 'ariali.ttf'),
        }

        if all(os.path.exists(p) for p in arial_paths.values()):
            try:
                pdf.add_font('Arial', '', arial_paths[''], uni=True)
                pdf.add_font('Arial', 'B', arial_paths['B'], uni=True)
                pdf.add_font('Arial', 'I', arial_paths['I'], uni=True)
                PDFGenerator._fonts_registered = True
                return True
            except Exception:
                pass

        PDFGenerator._fonts_registered = True
        return False

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Replace Unicode characters not supported by basic PDF fonts with ASCII equivalents."""
        replacements = {
            '\u2013': '-',   # en-dash
            '\u2014': '--',  # em-dash
            '\u2018': "'",   # left single quote
            '\u2019': "'",   # right single quote
            '\u201c': '"',   # left double quote
            '\u201d': '"',   # right double quote
            '\u2022': '*',   # bullet
            '\u2026': '...', # ellipsis
            '\u00a0': ' ',   # non-breaking space
            '\u00b0': ' deg', # degree
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    @staticmethod
    @staticmethod
    def generate_resume_pdf(resume_text: str, title: str = "Tailored Resume") -> bytes:
        """
        Convert plain resume text into a PDF byte stream optimized to fit on one page.
        Uses compact font sizes and tight spacing to ensure all content fits on a single page.

        Args:
            resume_text: The formatted resume text (plain text, may contain line breaks)
            title: Document title (displayed in PDF metadata)

        Returns:
            bytes: PDF file content as bytes, ready for upload to Supabase
        """
        try:
            from fpdf import FPDF
        except ImportError:
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                from reportlab.lib.colors import HexColor
                from io import BytesIO

                return PDFGenerator._generate_pdf_with_reportlab(resume_text, title)
            except ImportError:
                raise ImportError(
                    "PDF generation requires either 'fpdf2' or 'reportlab' to be installed."
                )

        # Sanitize text to handle Unicode characters not supported by basic fonts
        resume_text = PDFGenerator._sanitize_text(resume_text)

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=8)
        pdf.add_page()

        # Register Unicode fonts and determine which family to use
        unicode_available = PDFGenerator._register_fonts(pdf)
        font_family = "Arial" if unicode_available else "Helvetica"

        if not unicode_available:
            logger.warning(
                "Arial Unicode font not found. Falling back to Helvetica. "
                "Unicode characters (en-dash, bullets, etc.) may not render correctly."
            )

        # Compact margins (8mm each side gives ~190mm usable width)
        pdf.set_left_margin(8)
        pdf.set_right_margin(8)
        pdf.set_top_margin(8)

        # Only render title and separator if title is not empty
        if title:
            pdf.set_font(font_family, "B", 11)
            pdf.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(2)

            # Thin horizontal separator line
            pdf.set_draw_color(0, 150, 136)
            pdf.set_line_width(0.3)
            pdf.line(8, pdf.get_y(), 202, pdf.get_y())
            pdf.ln(3)

        # Body text - compact 9pt font for single-page fit
        pdf.set_font(font_family, "", 9)
        pdf.set_text_color(33, 33, 33)

        lines = resume_text.split('\n')
        for line in lines:
            stripped = line.strip()
            if not stripped:
                pdf.ln(1.5)
                continue

            is_header = stripped.isupper() or (stripped.endswith(':') and len(stripped) < 40)
            if is_header:
                pdf.set_font(font_family, "B", 10)
                pdf.set_text_color(0, 80, 70)
                pdf.cell(0, 4.5, stripped, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font(font_family, "", 9)
                pdf.set_text_color(33, 33, 33)
                pdf.ln(1)
            else:
                pdf.multi_cell(0, 4.2, stripped)
                pdf.ln(0.5)

        return bytes(pdf.output())

    @staticmethod
    def _generate_pdf_with_reportlab(resume_text: str, title: str = "Tailored Resume") -> bytes:
        """Fallback PDF generator used when fpdf is unavailable."""
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        text = PDFGenerator._sanitize_text(resume_text or "")
        story = []
        styles = getSampleStyleSheet()

        if title:
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))

        for line in text.split('\n'):
            if not line.strip():
                story.append(Spacer(1, 6))
                continue
            story.append(Paragraph(line.strip(), styles['BodyText']))

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        doc.build(story)
        return buffer.getvalue()
