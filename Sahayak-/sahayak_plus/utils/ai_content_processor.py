import os
import json
import sqlite3
from datetime import datetime
from .gemini_api import gemini_text, gemini_multimodal
from .diksha_api import diksha_extractor

class AIContentProcessor:
    def __init__(self):
        self.gemini_model = "gemini-2.0-flash-exp"
        self.db_path = 'sahayak_plus.db'
        
    def get_content_for_processing(self, book_id):
        """Get content from database for AI processing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM diksha_books WHERE book_id = ?
            ''', (book_id,))
            
            book = cursor.fetchone()
            conn.close()
            
            if not book:
                print(f"❌ Book not found in database: {book_id}")
                return None
            
            # Parse content items
            content_items = json.loads(book[8]) if book[8] else []
            
            return {
                'book_id': book[1],
                'title': book[2],
                'subject': json.loads(book[3]) if book[3] else [],
                'grade_level': json.loads(book[4]) if book[4] else [],
                'board': json.loads(book[5]) if book[5] else [],
                'medium': json.loads(book[6]) if book[6] else [],
                'description': book[7],
                'content_items': content_items,
                'download_date': book[9]
            }
            
        except Exception as e:
            print(f"❌ Error getting content for processing: {e}")
            return None
    
    def process_diksha_content(self, book_id, action_type='summarize'):
        """Process DIKSHA content with AI"""
        try:
            print(f"🧠 Processing content for book ID: {book_id}")
            
            # Get content from database
            content_data = self.get_content_for_processing(book_id)
            
            if not content_data:
                print("❌ No content found for processing")
                return {'error': 'No content found for processing'}
            
            print(f"✅ Found content: {content_data['title']}")
            
            # Process based on action type
            if action_type == 'summarize':
                return self.generate_summary(content_data)
            elif action_type == 'quiz':
                return self.generate_quiz(content_data)
            elif action_type == 'worksheet':
                return self.generate_worksheet(content_data)
            elif action_type == 'mcq':
                return self.generate_mcq(content_data)
            else:
                return {'error': f'Unknown action type: {action_type}'}
                
        except Exception as e:
            print(f"❌ Error processing content: {e}")
            return {'error': f'Error processing content: {str(e)}'}
    
    def generate_summary(self, content_data):
        """Generate summary for content"""
        try:
            # Create a comprehensive prompt for summary
            subject = content_data.get('subject', ['General'])
            if isinstance(subject, list):
                subject = subject[0] if subject else 'General'
            
            grade = content_data.get('grade_level', ['Class 10'])
            if isinstance(grade, list):
                grade = grade[0] if grade else 'Class 10'
            
            # Get content from items
            content_text = ""
            for item in content_data.get('content_items', []):
                content_text += f"\n{item.get('name', 'Unknown')}: {item.get('content', 'No content available')}"
            
            if not content_text.strip():
                content_text = f"Content about {subject} for {grade} students"
            
            prompt = f"""
            Create a comprehensive, student-friendly summary of the following educational content:
            
            Subject: {subject}
            Grade Level: {grade}
            Title: {content_data.get('title', 'Unknown')}
            
            Content:
            {content_text}
            
            Please provide:
            1. A clear overview of the main topics
            2. Key concepts and definitions
            3. Important points for students to remember
            4. Learning objectives
            
            Make it engaging and easy to understand for {grade} students.
            """
            
            summary = gemini_text(prompt)
            
            return {
                'summary': {
                    'content': summary,
                    'subject': subject,
                    'grade_level': grade,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return {'error': f'Error generating summary: {str(e)}'}
    
    def generate_quiz(self, content_data):
        """Generate quiz questions for content"""
        try:
            subject = content_data.get('subject', ['General'])
            if isinstance(subject, list):
                subject = subject[0] if subject else 'General'
            
            grade = content_data.get('grade_level', ['Class 10'])
            if isinstance(grade, list):
                grade = grade[0] if grade else 'Class 10'
            
            content_text = ""
            for item in content_data.get('content_items', []):
                content_text += f"\n{item.get('name', 'Unknown')}: {item.get('content', 'No content available')}"
            
            if not content_text.strip():
                content_text = f"Content about {subject} for {grade} students"
            
            prompt = f"""
            Create an engaging quiz based on the following educational content:
            
            Subject: {subject}
            Grade Level: {grade}
            Title: {content_data.get('title', 'Unknown')}
            
            Content:
            {content_text}
            
            Please create:
            1. 5 multiple choice questions with 4 options each
            2. 3 short answer questions
            3. 2 true/false questions
            4. Answer key for all questions
            
            Make the questions appropriate for {grade} students and cover the main concepts.
            """
            
            quiz = gemini_text(prompt)
            
            return {
                'quiz': {
                    'content': quiz,
                    'subject': subject,
                    'grade_level': grade,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating quiz: {e}")
            return {'error': f'Error generating quiz: {str(e)}'}
    
    def generate_worksheet(self, content_data):
        """Generate worksheet for content"""
        try:
            subject = content_data.get('subject', ['General'])
            if isinstance(subject, list):
                subject = subject[0] if subject else 'General'
            
            grade = content_data.get('grade_level', ['Class 10'])
            if isinstance(grade, list):
                grade = grade[0] if grade else 'Class 10'
            
            content_text = ""
            for item in content_data.get('content_items', []):
                content_text += f"\n{item.get('name', 'Unknown')}: {item.get('content', 'No content available')}"
            
            if not content_text.strip():
                content_text = f"Content about {subject} for {grade} students"
            
            prompt = f"""
            Create a comprehensive worksheet based on the following educational content:
            
            Subject: {subject}
            Grade Level: {grade}
            Title: {content_data.get('title', 'Unknown')}
            
            Content:
            {content_text}
            
            Please create:
            1. Fill-in-the-blank exercises
            2. Matching exercises
            3. Short answer questions
            4. Problem-solving activities (if applicable)
            5. Creative activities related to the topic
            
            Make it engaging and appropriate for {grade} students.
            """
            
            worksheet = gemini_text(prompt)
            
            return {
                'worksheet': {
                    'content': worksheet,
                    'subject': subject,
                    'grade_level': grade,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating worksheet: {e}")
            return {'error': f'Error generating worksheet: {str(e)}'}
    
    def generate_mcq(self, content_data):
        """Generate MCQ questions for content"""
        try:
            subject = content_data.get('subject', ['General'])
            if isinstance(subject, list):
                subject = subject[0] if subject else 'General'
            
            grade = content_data.get('grade_level', ['Class 10'])
            if isinstance(grade, list):
                grade = grade[0] if grade else 'Class 10'
            
            content_text = ""
            for item in content_data.get('content_items', []):
                content_text += f"\n{item.get('name', 'Unknown')}: {item.get('content', 'No content available')}"
            
            if not content_text.strip():
                content_text = f"Content about {subject} for {grade} students"
            
            prompt = f"""
            Create multiple choice questions (MCQs) based on the following educational content:
            
            Subject: {subject}
            Grade Level: {grade}
            Title: {content_data.get('title', 'Unknown')}
            
            Content:
            {content_text}
            
            Please create:
            1. 10 MCQs with 4 options each (A, B, C, D)
            2. Clear and unambiguous questions
            3. Only one correct answer per question
            4. Answer key with explanations
            5. Difficulty level appropriate for {grade} students
            
            Format each question clearly with question number, question text, options, and correct answer.
            """
            
            mcq = gemini_text(prompt)
            
            return {
                'mcq': {
                    'content': mcq,
                    'subject': subject,
                    'grade_level': grade,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating MCQs: {e}")
            return {'error': f'Error generating MCQs: {str(e)}'}
    
    def analyze_content_with_ai(self, book_id, analysis_type='comprehensive'):
        """Analyze content comprehensively with AI"""
        try:
            content_data = self.get_content_for_processing(book_id)
            
            if not content_data:
                return {'error': 'No content found for analysis'}
            
            # Generate comprehensive analysis
            subject = content_data.get('subject', ['General'])
            if isinstance(subject, list):
                subject = subject[0] if subject else 'General'
            
            grade = content_data.get('grade_level', ['Class 10'])
            if isinstance(grade, list):
                grade = grade[0] if grade else 'Class 10'
            
            content_text = ""
            for item in content_data.get('content_items', []):
                content_text += f"\n{item.get('name', 'Unknown')}: {item.get('content', 'No content available')}"
            
            if not content_text.strip():
                content_text = f"Content about {subject} for {grade} students"
            
            prompt = f"""
            Provide a comprehensive analysis of the following educational content:
            
            Subject: {subject}
            Grade Level: {grade}
            Title: {content_data.get('title', 'Unknown')}
            
            Content:
            {content_text}
            
            Please analyze:
            1. Content structure and organization
            2. Learning objectives and outcomes
            3. Difficulty level and appropriateness for {grade}
            4. Key concepts and their importance
            5. Suggested teaching strategies
            6. Assessment recommendations
            7. Areas for improvement or enhancement
            
            Provide detailed insights that would help teachers use this content effectively.
            """
            
            analysis = gemini_text(prompt)
            
            return {
                'analysis': {
                    'content': analysis,
                    'subject': subject,
                    'grade_level': grade,
                    'analysis_type': analysis_type,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error analyzing content: {e}")
            return {'error': f'Error analyzing content: {str(e)}'}
    
    def create_teaching_plan(self, book_id, grade_level='multi-grade', duration_weeks=12):
        """Create a teaching plan from content"""
        try:
            content_data = self.get_content_for_processing(book_id)
            
            if not content_data:
                return {'error': 'No content found for teaching plan'}
            
            subject = content_data.get('subject', ['General'])
            if isinstance(subject, list):
                subject = subject[0] if subject else 'General'
            
            grade = content_data.get('grade_level', ['Class 10'])
            if isinstance(grade, list):
                grade = grade[0] if grade else 'Class 10'
            
            content_text = ""
            for item in content_data.get('content_items', []):
                content_text += f"\n{item.get('name', 'Unknown')}: {item.get('content', 'No content available')}"
            
            if not content_text.strip():
                content_text = f"Content about {subject} for {grade} students"
            
            prompt = f"""
            Create a detailed {duration_weeks}-week teaching plan based on the following educational content:
            
            Subject: {subject}
            Grade Level: {grade}
            Title: {content_data.get('title', 'Unknown')}
            
            Content:
            {content_text}
            
            Please create:
            1. Weekly breakdown of topics
            2. Learning objectives for each week
            3. Teaching activities and methods
            4. Assessment strategies
            5. Resources and materials needed
            6. Timeline for each lesson
            7. Differentiation strategies for multi-grade classroom
            
            Make it practical and implementable for teachers in a {grade_level} classroom.
            """
            
            teaching_plan = gemini_text(prompt)
            
            return {
                'teaching_plan': {
                    'content': teaching_plan,
                    'subject': subject,
                    'grade_level': grade,
                    'duration_weeks': duration_weeks,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error creating teaching plan: {e}")
            return {'error': f'Error creating teaching plan: {str(e)}'}

# Global instance
ai_processor = AIContentProcessor() 