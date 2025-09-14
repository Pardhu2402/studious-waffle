import os
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file, make_response
from sahayak_plus.utils.gemini_api import gemini_text, gemini_multimodal
from sahayak_plus.utils.youtube_api import youtube_search
from sahayak_plus.utils.pdf_generator import create_worksheet_pdf, create_simple_pdf, generate_ai_content_pdf
from sahayak_plus.utils.diksha_api import diksha_extractor
from sahayak_plus.utils.ai_content_processor import ai_processor
from werkzeug.utils import secure_filename
from io import BytesIO
import sqlite3
from sahayak_plus.utils.free_education_apis import free_apis
import requests
import google.generativeai as genai
from PIL import Image
import wave
from google.api_core.client_options import ClientOptions

# Load environment variables

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For session

# Database setup
def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect('sahayak_plus.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create DIKSHA books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diksha_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            subject TEXT,
            grade_level TEXT,
            board TEXT,
            medium TEXT,
            description TEXT,
            content_items TEXT,
            download_date TEXT
        )
    ''')
    
    # Create imported content table for free APIs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imported_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content_data TEXT,
            import_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            value TEXT,
            student_id TEXT,
            lesson_id TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# In-memory data storage (replace with database in production)
SAVED_RESPONSES = []
SAVED_WORKSHEETS = []
TEACHER_PROFILES = {
    'default': {
        'name': 'Mrs. Kavitha',
        'school': 'Govt School, Vizag',
        'subjects': ['Science', 'Math', 'English'],
        'prompts_count': 42,
        'worksheets_count': 133,
        'badges': ['Worksheet Wizard', 'Early Prompter', 'Language Pro'],
        'avatar': '👩‍🏫'
    }
}
SOCIAL_FEED = []
TRENDING_PROMPTS = [
    "Create a Hindi story about soil types for 5th grade",
    "Explain water cycle in Telugu with worksheet",
    "Math games for multi-grade classroom",
    "Festival activities for primary students"
]

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure Gemini API key (set in environment or here)
# genai.configure(api_key="YOUR_API_KEY")

try:
    from google.generativeai import types
except ImportError:
    types = None

# === Dialogflow CX Chat Endpoint ===
import uuid
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.oauth2 import service_account

# Dialogflow CX agent details (set your agent_id and language_code)
DIALOGFLOW_PROJECT_ID = "intigrationagent"
DIALOGFLOW_AGENT_ID = "3aad3579-2ae7-4556-98af-4b8904583c71"
DIALOGFLOW_LOCATION = "us-central1"
DIALOGFLOW_LANGUAGE_CODE = "en"
DIALOGFLOW_CREDENTIALS_FILE = "/Users/sreemadhav/SreeMadhav/Mhv CODES/Google Agentic AI/PS2/sahayak_plus/intigrationagent-96cdbb2bb69c.json"

dialogflow_credentials = service_account.Credentials.from_service_account_file(DIALOGFLOW_CREDENTIALS_FILE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get('text', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400

        client_options = ClientOptions(api_endpoint=f"{DIALOGFLOW_LOCATION}-dialogflow.googleapis.com")
        client = dialogflowcx.SessionsClient(credentials=dialogflow_credentials, client_options=client_options)
        session_path = client.session_path(DIALOGFLOW_PROJECT_ID, DIALOGFLOW_LOCATION, DIALOGFLOW_AGENT_ID, session_id)

        text_input = dialogflowcx.TextInput(text=user_input)
        query_input = dialogflowcx.QueryInput(text=text_input, language_code=DIALOGFLOW_LANGUAGE_CODE)

        response = client.detect_intent(
            request={
                "session": session_path,
                "query_input": query_input
            }
        )

        agent_responses = []
        for msg in response.query_result.response_messages:
            if msg.text and msg.text.text:
                agent_responses.extend(msg.text.text)

        # YouTube video recommendations
        videos = youtube_search(user_input)

        return jsonify({
            'response': agent_responses[0] if agent_responses else "",
            'all_responses': agent_responses,
            'session_id': session_id,
            'videos': videos
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return render_template('home.html', feed=SOCIAL_FEED, trending=TRENDING_PROMPTS)

@app.route('/feed')
def feed():
    return render_template('feed.html', feed=SOCIAL_FEED, trending=TRENDING_PROMPTS)

@app.route('/profile')
def profile():
    teacher_id = session.get('teacher_id', 'default')
    profile = TEACHER_PROFILES.get(teacher_id, TEACHER_PROFILES['default'])
    return render_template('profile.html', profile=profile)

@app.route('/tools', methods=['GET', 'POST'])
def tools():
    gemini_response = None
    yt_search_url = None
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            # Unified AI response with videos and worksheet
            gemini_response = gemini_text(query)
            yt_search_url = youtube_search(query)
            
            # Add to social feed
            feed_post = {
                'id': len(SOCIAL_FEED) + 1,
                'teacher': TEACHER_PROFILES['default']['name'],
                'avatar': TEACHER_PROFILES['default']['avatar'],
                'prompt': query,
                'response': gemini_response,
                'videos': yt_search_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'likes': 0,
                'comments': []
            }
            SOCIAL_FEED.insert(0, feed_post)
            
    return render_template('tools.html', gemini_response=gemini_response, yt_search_url=yt_search_url, trending=TRENDING_PROMPTS)

@app.route('/unified_ai', methods=['POST'])
def unified_ai():
    """Unified AI endpoint that generates text, worksheet, and videos together"""
    try:
        data = request.json
        query = data.get('query')
        grade = data.get('grade', 'multi-grade')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Generate AI response
        ai_response = gemini_text(query)
        
        # Generate worksheet
        worksheet_prompt = f"Create a worksheet for: {query} for {grade} students"
        worksheet = gemini_text(worksheet_prompt)
        
        # Get YouTube videos
        videos = youtube_search(query)
        
        # Create feed post
        feed_post = {
            'id': len(SOCIAL_FEED) + 1,
            'teacher': TEACHER_PROFILES['default']['name'],
            'avatar': TEACHER_PROFILES['default']['avatar'],
            'prompt': query,
            'response': ai_response,
            'worksheet': worksheet,
            'videos': videos,
            'grade': grade,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'likes': 0,
            'comments': []
        }
        SOCIAL_FEED.insert(0, feed_post)
        
        return jsonify({
            'ai_response': ai_response,
            'worksheet': worksheet,
            'videos': videos,
            'feed_post': feed_post
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_response', methods=['POST'])
def save_response():
    data = request.json
    SAVED_RESPONSES.append(data)
    return jsonify({'status': 'success'})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', responses=SAVED_RESPONSES, worksheets=SAVED_WORKSHEETS)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    file = request.files['image']
    grade = request.form.get('grade', 'multi-grade')
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        worksheet = gemini_multimodal(filepath, grade)
        SAVED_WORKSHEETS.append({'worksheet': worksheet, 'grade': grade})
        return jsonify({'worksheet': worksheet})
    return jsonify({'error': 'No file uploaded'}), 400

@app.route('/download_worksheet/<int:index>')
def download_worksheet(index):
    worksheet = SAVED_WORKSHEETS[index]['worksheet']
    return send_file(BytesIO(worksheet.encode()), as_attachment=True, download_name=f'worksheet_{index+1}.txt')

@app.route('/download_worksheet_pdf/<int:index>')
def download_worksheet_pdf(index):
    """Download worksheet as a beautiful PDF"""
    try:
        worksheet_data = SAVED_WORKSHEETS[index]
        worksheet_content = worksheet_data['worksheet']
        grade = worksheet_data['grade']
        
        # Create PDF
        pdf_content = create_worksheet_pdf(worksheet_content, grade)
        
        # Create BytesIO object for the PDF
        pdf_buffer = BytesIO(pdf_content)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'sahayak_worksheet_{index+1}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

@app.route('/download_worksheet_pdf', methods=['POST'])
def download_worksheet_pdf_form():
    """Download worksheet as PDF from form submission"""
    try:
        worksheet_content = request.form.get('worksheet')
        grade = request.form.get('grade', 'multi-grade')
        
        if not worksheet_content:
            return jsonify({'error': 'No worksheet content provided'}), 400
        
        # Create PDF
        pdf_content = create_worksheet_pdf(worksheet_content, grade)
        
        # Create BytesIO object for the PDF
        pdf_buffer = BytesIO(pdf_content)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'sahayak_worksheet.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

@app.route('/preview_worksheet_pdf', methods=['POST'])
def preview_worksheet_pdf():
    """Preview worksheet as PDF inline on website"""
    try:
        worksheet_content = request.form.get('worksheet')
        grade = request.form.get('grade', 'multi-grade')
        
        if not worksheet_content:
            return jsonify({'error': 'No worksheet content provided'}), 400
        
        # Create PDF
        pdf_content = create_worksheet_pdf(worksheet_content, grade)
        
        # Convert PDF to base64 for inline display
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return jsonify({
            'pdf_data': pdf_base64,
            'filename': f'sahayak_worksheet_{grade.replace(" ", "_")}.pdf'
        })
    except Exception as e:
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    """Like a social feed post"""
    for post in SOCIAL_FEED:
        if post['id'] == post_id:
            post['likes'] += 1
            return jsonify({'likes': post['likes']})
    return jsonify({'error': 'Post not found'}), 404

@app.route('/comment_post/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    """Add comment to a social feed post"""
    data = request.json
    comment = data.get('comment')
    
    for post in SOCIAL_FEED:
        if post['id'] == post_id:
            post['comments'].append({
                'teacher': TEACHER_PROFILES['default']['name'],
                'comment': comment,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
            return jsonify({'status': 'success'})
    return jsonify({'error': 'Post not found'}), 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# DIKSHA Content Management Routes
@app.route('/diksha')
def diksha_library():
    """DIKSHA Content Library page"""
    return render_template('diksha_library.html')

@app.route('/diksha/search', methods=['POST'])
def diksha_search():
    """Search DIKSHA content"""
    try:
        data = request.json
        query = data.get('query', '')
        filters = data.get('filters', {})
        
        # Search DIKSHA content
        content = diksha_extractor.search_content(filters)
        
        return jsonify({
            'success': True,
            'content': content,
            'count': len(content)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/diksha/download', methods=['POST'])
def diksha_download():
    """Download and extract DIKSHA content"""
    try:
        data = request.json
        book_id = data.get('book_id')
        
        if not book_id:
            return jsonify({'success': False, 'error': 'Book ID required'}), 400
        
        print(f"🔍 Searching for book ID: {book_id}")  # Debug log
        
        # First, search for the book with different filters
        search_attempts = [
            {},  # Default search
            {"board": ["CBSE"]},
            {"board": ["CBSE"], "medium": ["English"]},
            {"board": ["CBSE"], "medium": ["English"], "gradeLevel": ["Class 10"]}
        ]
        
        book_data = None
        content = []
        
        for attempt, filters in enumerate(search_attempts):
            print(f"🔍 Search attempt {attempt + 1} with filters: {filters}")
            content = diksha_extractor.search_content(filters)
            
            if content:
                print(f"📚 Found {len(content)} books in attempt {attempt + 1}")
                for book in content:
                    if book.get('identifier') == book_id:
                        book_data = book
                        print(f"✅ Found matching book: {book.get('name', 'Unknown')}")
                        break
                
                if book_data:
                    break
            else:
                print(f"❌ No content found in attempt {attempt + 1}")
        
        if not book_data:
            # If we still can't find it, try to get any available book for demo
            print("⚠️ Book not found, trying to get sample content")
            sample_filters = {
                "board": ["CBSE"],
                "medium": ["English"],
                "gradeLevel": ["Class 10"],
                "contentType": ["TextBook"]
            }
            sample_content = diksha_extractor.search_content(sample_filters)
            
            if sample_content:
                book_data = sample_content[0]
                print(f"📚 Using sample book: {book_data.get('name', 'Unknown')}")
            else:
                return jsonify({'success': False, 'error': 'No content available for download'}), 404
        
        if not book_data:
            return jsonify({'success': False, 'error': 'Book not found in any search attempt'}), 404
        
        # Download and extract the book
        print(f"📥 Starting download for: {book_data.get('name', 'Unknown')}")
        result = diksha_extractor.download_and_extract_book(book_data)
        
        if result:
            print(f"✅ Download successful: {result['title']}")
            return jsonify({
                'success': True,
                'message': f'Successfully downloaded and extracted {result["title"]}',
                'book_id': result['book_id'],
                'content_items': len(result['content_items'])
            })
        else:
            print("❌ Download failed")
            return jsonify({'success': False, 'error': 'Failed to download content'}), 500
            
    except Exception as e:
        print(f"❌ Error in download: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/diksha/details/<book_id>')
def diksha_details(book_id):
    """Get details of a specific DIKSHA book"""
    try:
        print(f"🔍 Getting details for book ID: {book_id}")
        
        # First try to get from local database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM diksha_books WHERE book_id = ?
        ''', (book_id,))
        
        book = cursor.fetchone()
        conn.close()
        
        if book:
            print(f"✅ Found book in local database: {book[2]}")  # book[2] is title
            # Convert database row to dictionary
            book_data = {
                'book_id': book[1],
                'title': book[2],
                'subject': json.loads(book[3]) if book[3] else [],
                'grade_level': json.loads(book[4]) if book[4] else [],
                'board': json.loads(book[5]) if book[5] else [],
                'medium': json.loads(book[6]) if book[6] else [],
                'description': book[7],
                'content_items': json.loads(book[8]) if book[8] else [],
                'download_date': book[9]
            }
            
            return jsonify({
                'success': True,
                'content': book_data
            })
        else:
            print(f"❌ Book not found in local database: {book_id}")
            return jsonify({
                'success': False,
                'error': 'Book not found in local database. Please download it first.'
            }), 404
            
    except Exception as e:
        print(f"❌ Error getting book details: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving book details: {str(e)}'
        }), 500

@app.route('/diksha/local')
def diksha_local():
    """Get all locally downloaded DIKSHA content"""
    try:
        print("🔍 Fetching local DIKSHA content")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM diksha_books ORDER BY download_date DESC
        ''')
        
        books = cursor.fetchall()
        conn.close()
        
        print(f"✅ Found {len(books)} books in local database")
        
        # Convert database rows to dictionaries
        content = []
        for book in books:
            book_data = {
                'identifier': book[1],  # book_id
                'name': book[2],        # title
                'subject': json.loads(book[3]) if book[3] else [],
                'gradeLevel': json.loads(book[4]) if book[4] else [],
                'board': json.loads(book[5]) if book[5] else [],
                'medium': json.loads(book[6]) if book[6] else [],
                'description': book[7],
                'content_items': json.loads(book[8]) if book[8] else [],
                'download_date': book[9]
            }
            content.append(book_data)
        
        return jsonify({
            'success': True,
            'content': content
        })
        
    except Exception as e:
        print(f"❌ Error fetching local content: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving local content: {str(e)}'
        }), 500

@app.route('/diksha/process', methods=['POST'])
def diksha_process():
    """Process DIKSHA content with AI"""
    try:
        data = request.json
        book_id = data.get('book_id')
        action_type = data.get('action_type', 'summarize')
        
        if not book_id:
            return jsonify({'success': False, 'error': 'Book ID required'}), 400
        
        # Process content with AI
        results = ai_processor.process_diksha_content(book_id, action_type=action_type)
        
        if 'error' in results:
            return jsonify({'success': False, 'error': results['error']}), 500
        
        return jsonify({
            'success': True,
            'results': results,
            'action_type': action_type
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/diksha/analyze', methods=['POST'])
def diksha_analyze():
    """Analyze DIKSHA content comprehensively"""
    try:
        data = request.json
        book_id = data.get('book_id')
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        if not book_id:
            return jsonify({'success': False, 'error': 'Book ID required'}), 400
        
        # Analyze content
        analysis = ai_processor.analyze_content_with_ai(book_id, analysis_type)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']}), 500
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/diksha/teaching-plan', methods=['POST'])
def diksha_teaching_plan():
    """Create teaching plan from DIKSHA content"""
    try:
        data = request.json
        book_id = data.get('book_id')
        grade_level = data.get('grade_level', 'multi-grade')
        duration_weeks = data.get('duration_weeks', 12)
        
        if not book_id:
            return jsonify({'success': False, 'error': 'Book ID required'}), 400
        
        # Create teaching plan
        teaching_plan = ai_processor.create_teaching_plan(book_id, grade_level, duration_weeks)
        
        if 'error' in teaching_plan:
            return jsonify({'success': False, 'error': teaching_plan['error']}), 500
        
        return jsonify({
            'success': True,
            'teaching_plan': teaching_plan
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/diksha/sample')
def diksha_sample():
    """Download sample DIKSHA content for demonstration"""
    try:
        # Search for sample content (CBSE Class 10 Science)
        filters = {
            "board": ["CBSE"],
            "medium": ["English"],
            "gradeLevel": ["Class 10"],
            "contentType": ["TextBook"],
            "subject": ["Science"]
        }
        
        content = diksha_extractor.search_content(filters)
        
        if content:
            # Download the first book
            result = diksha_extractor.download_and_extract_book(content[0])
            
            if result:
                return jsonify({
                    'success': True,
                    'message': f'Successfully downloaded sample content: {result["title"]}',
                    'book_id': result['book_id']
                })
        
        return jsonify({'success': False, 'error': 'No sample content available'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    """Analytics dashboard page"""
    return render_template('analytics.html')

@app.route('/analytics/data')
def analytics_data():
    """Get analytics data"""
    try:
        # Get metrics from database
        conn = sqlite3.connect(diksha_extractor.db_path)
        cursor = conn.cursor()
        
        # Count books
        cursor.execute('SELECT COUNT(*) FROM content_books')
        diksha_books = cursor.fetchone()[0]
        
        # Count content items
        cursor.execute('SELECT COUNT(*) FROM content_items')
        content_items = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute('''
            SELECT action_type, timestamp 
            FROM content_analytics 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        activities = cursor.fetchall()
        
        conn.close()
        
        # Format recent activity
        recent_activity = []
        for activity in activities:
            action_type = activity[0]
            timestamp = activity[1]
            
            icons = {
                'summarize': '📝',
                'quiz': '❓',
                'worksheet': '📄',
                'mcq': '🎯',
                'download': '⬇️',
                'process': '🧠'
            }
            
            titles = {
                'summarize': 'Generated Summary',
                'quiz': 'Created Quiz',
                'worksheet': 'Generated Worksheet',
                'mcq': 'Generated MCQs',
                'download': 'Downloaded Content',
                'process': 'Processed Content'
            }
            
            recent_activity.append({
                'icon': icons.get(action_type, '📊'),
                'title': titles.get(action_type, 'Activity'),
                'timestamp': timestamp,
                'duration': '2 min ago'
            })
        
        # Mock metrics for now (in real app, these would come from actual usage tracking)
        metrics = {
            'ai_requests': 156,
            'worksheets_generated': 89,
            'diksha_books': diksha_books,
            'content_items': content_items,
            'summaries_generated': 45,
            'quizzes_created': 32,
            'worksheets_made': 89,
            'mcqs_generated': 67
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/diksha/download-ai-result', methods=['POST'])
def download_ai_result():
    """Download AI-generated content as PDF"""
    try:
        data = request.json
        action_type = data.get('action_type')
        item_name = data.get('item_name')
        content = data.get('content')
        
        if not all([action_type, item_name, content]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        # Generate PDF using reportlab
        pdf_buffer = generate_ai_content_pdf(content, action_type, item_name)
        
        # Create response with PDF
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{item_name}_{action_type}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'success': False, 'error': f'Error generating PDF: {str(e)}'}), 500

# Free Education APIs Routes
@app.route('/free-apis')
def free_apis_page():
    """Free Education APIs page"""
    return render_template('free_apis.html')

@app.route('/api/openlibrary/search', methods=['POST'])
def openlibrary_search():
    """Search books using Open Library API"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query required'}), 400
        
        result = free_apis.search_openlibrary_books(query, limit)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nasa/search', methods=['POST'])
def nasa_search():
    """Search images and videos using NASA API"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query required'}), 400
        
        result = free_apis.search_nasa_images(query, limit)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wikipedia/summary', methods=['POST'])
def wikipedia_summary():
    """Get topic summary from Wikipedia API"""
    try:
        data = request.json
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic required'}), 400
        
        result = free_apis.get_wikipedia_summary(topic)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/opentrivia/categories')
def opentrivia_categories():
    """Get available categories from Open Trivia DB"""
    try:
        result = free_apis.get_opentrivia_categories()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/opentrivia/quiz', methods=['POST'])
def opentrivia_quiz():
    """Get quiz questions from Open Trivia DB"""
    try:
        data = request.json
        category = data.get('category', 9)  # Default to General Knowledge
        difficulty = data.get('difficulty', 'easy')
        amount = data.get('amount', 5)
        question_type = data.get('type', 'multiple')
        
        result = free_apis.get_opentrivia_quiz(category, difficulty, amount, question_type)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wikipedia/quiz', methods=['POST'])
def wikipedia_quiz():
    """Generate quiz from Wikipedia summary"""
    try:
        data = request.json
        topic = data.get('topic', '')
        num_questions = data.get('num_questions', 5)
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic required'}), 400
        
        result = free_apis.generate_quiz_from_wikipedia(topic, num_questions)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/free-apis/import', methods=['POST'])
def import_free_content():
    """Import content from free APIs to Sahayak+ library"""
    try:
        data = request.json
        content_type = data.get('type')  # 'book', 'image', 'summary', 'quiz'
        content_data = data.get('content')
        title = data.get('title', 'Imported Content')
        
        if not content_type or not content_data:
            return jsonify({'success': False, 'error': 'Content type and data required'}), 400
        
        # Save to database (you can extend this based on your needs)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO imported_content (type, title, content_data, import_date)
            VALUES (?, ?, ?, ?)
        ''', (content_type, title, json.dumps(content_data), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {content_type}',
            'content_id': cursor.lastrowid
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/free-apis/imported')
def get_imported_content():
    """Get all imported content from free APIs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, type, title, content_data, import_date 
            FROM imported_content 
            ORDER BY import_date DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        content = []
        for row in rows:
            content.append({
                'id': row[0],
                'type': row[1],
                'title': row[2],
                'content': json.loads(row[3]) if row[3] else {},
                'import_date': row[4]
            })
        
        return jsonify({
            'success': True,
            'content': content
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/free-apis/delete/<int:content_id>', methods=['DELETE'])
def delete_imported_content(content_id):
    """Delete imported content"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM imported_content WHERE id = ?', (content_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Content deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/free-apis/process', methods=['POST'])
def process_imported_content():
    """Process imported content with AI (summary, quiz, worksheet, mcq)"""
    try:
        data = request.json
        content_id = data.get('content_id')
        action_type = data.get('action_type', 'summarize')
        if not content_id:
            return jsonify({'success': False, 'error': 'Content ID required'}), 400
        # Fetch imported content from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT content_data, type, title FROM imported_content WHERE id = ?', (content_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return jsonify({'success': False, 'error': 'Imported content not found'}), 404
        content_data, content_type, title = row
        # Use the main text for AI processing
        content = json.loads(content_data)
        # Choose what to send to AI based on type
        if content_type == 'book':
            prompt = f"Summarize the following book for teachers and students: {content.get('title', '')}\nAuthor: {content.get('author', '')}\nYear: {content.get('year', '')}"
        elif content_type == 'image':
            prompt = f"Describe this image for classroom use: {content.get('title', '')}\nDescription: {content.get('description', '')}"
        elif content_type == 'summary':
            prompt = f"Summarize or create a worksheet/quiz for this topic: {content.get('title', '')}\n{content.get('extract', '')}"
        elif content_type == 'quiz':
            prompt = f"Format the following quiz for classroom use: {content.get('title', '')}\n{content}"
        else:
            prompt = f"Process this content for classroom use: {title}\n{content}"
        # Modify prompt for action_type
        if action_type == 'quiz':
            prompt = f"Create a quiz based on the following content for students. {prompt}"
        elif action_type == 'worksheet':
            prompt = f"Create a worksheet based on the following content for students. {prompt}"
        elif action_type == 'mcq':
            prompt = f"Create multiple choice questions (MCQs) based on the following content for students. {prompt}"
        # Call Gemini AI
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        ai_result = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        results = {title: {'content': ai_result}}
        return jsonify({'success': True, 'results': results, 'action_type': action_type})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/free-apis/download-ai-result', methods=['POST'])
def download_imported_ai_result():
    """Download AI-generated content for imported content as PDF"""
    try:
        data = request.json
        action_type = data.get('action_type')
        item_name = data.get('item_name')
        content = data.get('content')
        if not all([action_type, item_name, content]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        pdf_buffer = generate_ai_content_pdf(content, action_type, item_name)
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{item_name}_{action_type}.pdf"'
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error generating PDF: {str(e)}'}), 500

@app.route('/wireframe')
def wireframe():
    return render_template('wireframe.html')

# ===================== AGENTIC FEATURE ENDPOINTS (SCAFFOLD) =====================

# 1. Wellbeing Agent: Teacher wellbeing analysis, nudges
@app.route('/wellbeing/analyze', methods=['POST'])
def wellbeing_analyze():
    """Analyze teacher wellbeing and provide nudges."""
    data = request.json
    teacher_log = data.get('log') or data.get('text')
    if not teacher_log:
        return jsonify({'success': False, 'error': 'No teacher log/text provided'}), 400

    # 1. Analyze sentiment using Gemini
    sentiment_prompt = (
        "Analyze the following teacher log for signs of stress, burnout, or negative sentiment. "
        "Return a JSON object with fields: 'sentiment' (positive/neutral/negative), 'score' (0-1), and 'summary'.\nLog: " + teacher_log
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            sentiment_prompt,
        ])
        sentiment_result = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        # Try to parse as JSON, fallback to raw string
        try:
            import json as _json
            sentiment_json = _json.loads(sentiment_result)
        except Exception:
            sentiment_json = {'sentiment': 'unknown', 'score': 0.5, 'summary': sentiment_result}
    except Exception as e:
        return jsonify({'success': False, 'error': f'Gemini sentiment analysis failed: {str(e)}'}), 500

    # 2. If negative or neutral, generate a motivational nudge
    nudge = None
    if sentiment_json.get('sentiment', '').lower() in ['negative', 'neutral', 'unknown']:
        nudge_prompt = (
            "The following teacher log shows signs of stress or burnout. "
            "Write a short, positive, practical motivational nudge for the teacher.\nLog: " + teacher_log
        )
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([
                nudge_prompt,
            ])
            nudge = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        except Exception as e:
            nudge = f"Nudge generation failed: {str(e)}"
    else:
        nudge = "Keep up the great work!"

    # 3. (Optional) Store in DB for analytics (not implemented yet)
    # TODO: Save (teacher_log, sentiment_json, nudge, timestamp) to DB for analytics

    return jsonify({
        'success': True,
        'sentiment': sentiment_json,
        'nudge': nudge
    })

# 2. Feedback Agent: Student feedback (emoji, voice, webcam)
@app.route('/feedback/submit', methods=['POST'])
def feedback_submit():
    """Submit student feedback (emoji, voice, webcam)."""
    data = request.json
    feedback_type = data.get('type')  # 'emoji', 'voice', 'webcam'
    value = data.get('value')
    student_id = data.get('student_id')
    lesson_id = data.get('lesson_id')
    timestamp = datetime.now().isoformat()
    if not feedback_type or not value:
        return jsonify({'success': False, 'error': 'Missing feedback type or value'}), 400

    # Store feedback in SQLite
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                value TEXT,
                student_id TEXT,
                lesson_id TEXT,
                timestamp TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO feedback (type, value, student_id, lesson_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (feedback_type, value, student_id, lesson_id, timestamp))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Feedback submitted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 3. Feedback Agent: Feedback analytics for dashboard
@app.route('/feedback/analytics', methods=['GET'])
def feedback_analytics():
    """Get feedback analytics for dashboard visualization."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, value, COUNT(*) as count
            FROM feedback
            GROUP BY type, value
            ORDER BY type, value
        ''')
        rows = cursor.fetchall()
        conn.close()
        analytics = []
        for row in rows:
            analytics.append({
                'type': row['type'],
                'value': row['value'],
                'count': row['count']
            })
        return jsonify({'success': True, 'analytics': analytics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 4. Social Agent: Social media trend mining (Reddit, X, YouTube)
@app.route('/social/trends', methods=['GET'])
def social_trends():
    """Fetch and summarize social media teaching trends."""
    # TODO: Replace mock data with real API calls if keys are available
    try:
        # Mock trending posts from Reddit, X, YouTube
        mock_trends = [
            {'source': 'Reddit', 'title': 'Fun ways to teach fractions', 'content': 'Teachers share hands-on fraction activities.'},
            {'source': 'X', 'title': 'Classroom management hacks', 'content': 'Thread on keeping students engaged.'},
            {'source': 'YouTube', 'title': 'Science experiments for kids', 'content': 'Popular video: Easy science demos.'}
        ]
        # Summarize each using Gemini
        summarized = []
        for trend in mock_trends:
            prompt = f"Summarize this {trend['source']} post for teachers: {trend['title']} - {trend['content']}"
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content([
                    prompt,
                ])
                summary = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            except Exception as e:
                summary = f"Summary failed: {str(e)}"
            summarized.append({
                'source': trend['source'],
                'title': trend['title'],
                'summary': summary
            })
        return jsonify({'success': True, 'trends': summarized})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 5. Timetable Agent: Weather/context-aware timetable updates
@app.route('/timetable/update', methods=['POST'])
def timetable_update():
    """Update timetable based on weather or context."""
    data = request.json
    location = data.get('location', 'Vizag')
    # TODO: Integrate with OpenWeatherMap API. For now, use mock weather.
    try:
        # Mock weather data
        weather = {'location': location, 'forecast': 'rain', 'temp_c': 28}
        # Suggest timetable change if rain
        suggestion = None
        if weather['forecast'] == 'rain':
            suggestion = 'Reschedule PT period to indoor activity due to rain.'
        else:
            suggestion = 'No changes needed.'
        return jsonify({'success': True, 'weather': weather, 'suggestion': suggestion})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 6. Timetable Agent: Auto circular generation
@app.route('/timetable/circular', methods=['POST'])
def timetable_circular():
    """Auto-generate and send school/college circulars."""
    data = request.json
    event = data.get('event') or data.get('reason')
    if not event:
        return jsonify({'success': False, 'error': 'No event or reason provided'}), 400
    # Use Gemini to generate a circular
    prompt = f"Draft a short, formal school circular for the following event or reason: {event}"
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        circular = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'circular': circular})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 7. Peer Teaching Facilitator: Peer teaching script/grouping
@app.route('/peer-teaching/plan', methods=['POST'])
def peer_teaching_plan():
    """Generate peer teaching scripts and groupings."""
    data = request.json
    topic = data.get('topic')
    grade_pairs = data.get('grade_pairs')  # e.g., [4, 5]
    if not topic or not grade_pairs or not isinstance(grade_pairs, list) or len(grade_pairs) != 2:
        return jsonify({'success': False, 'error': 'Provide topic and grade_pairs (list of two grades)'}), 400
    # Use Gemini to generate script
    prompt = (
        f"Create a peer teaching script: Grade {grade_pairs[0]} teaches '{topic}' to Grade {grade_pairs[1]} using local context. "
        f"Also suggest how to group students for this activity."
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        script = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'script': script, 'grades': grade_pairs, 'topic': topic})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 8. NEP 2020 Compliance Agent: Compliance check
@app.route('/nep/check', methods=['POST'])
def nep_check():
    """Check content for NEP 2020/state compliance."""
    data = request.json
    content = data.get('content')
    if not content:
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    # Use Gemini to check compliance (mock guideline for now)
    guideline = "NEP 2020 and state guidelines for school content."
    prompt = (
        f"Verify if the following content aligns with {guideline}. "
        f"If not, suggest improvements.\nContent: {content}"
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        compliance_result = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'compliance': compliance_result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 9. AI Co-Teaching Agent: Real-time teaching gap detection
@app.route('/co-teaching/suggestions', methods=['POST'])
def co_teaching_suggestions():
    """Provide real-time teaching gap detection and suggestions."""
    data = request.json
    transcript = data.get('transcript')
    if not transcript:
        return jsonify({'success': False, 'error': 'No transcript provided'}), 400
    # Use Gemini to detect gaps and suggest improvements
    prompt = (
        "Analyze the following classroom transcript for teaching gaps, missed concepts, or unclear explanations. "
        "Suggest real-time tips or prompts for the teacher to improve the lesson.\nTranscript: " + transcript
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        suggestions = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'suggestions': suggestions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 10. Behavior Management Agent: Behavior analysis
@app.route('/behavior/analyze', methods=['POST'])
def behavior_analyze():
    """Analyze classroom behavior and suggest strategies."""
    data = request.json
    observation = data.get('observation')
    if not observation:
        return jsonify({'success': False, 'error': 'No observation provided'}), 400
    # Use Gemini to suggest strategies
    prompt = (
        "Given the following classroom behavior observation, suggest practical strategies for the teacher to manage and support all students, including neurodivergent learners.\nObservation: " + observation
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        strategies = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'strategies': strategies})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 11. Parental Engagement Agent: Reports, reminders, activities
@app.route('/parental/notify', methods=['POST'])
def parental_notify():
    """Send parental engagement reports, reminders, and activities."""
    data = request.json
    student_name = data.get('student_name')
    report = data.get('report') or data.get('reminder') or data.get('activity')
    language = data.get('language', 'English')
    if not student_name or not report:
        return jsonify({'success': False, 'error': 'Missing student_name or report/reminder/activity'}), 400
    # Use Gemini to generate a parent-friendly message
    prompt = (
        f"Write a short, positive message for the parent of {student_name} about the following: {report}. "
        f"Make it friendly and easy to understand."
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        message = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        # Mock translation if not English
        if language.lower() != 'english':
            message = f"[Translated to {language}] {message}"
        return jsonify({'success': True, 'message': message, 'language': language})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 12. Assessment Agent: Auto-grading and analytics
@app.route('/assessment/grade', methods=['POST'])
def assessment_grade():
    """Auto-grade assessments and provide analytics."""
    data = request.json
    questions = data.get('questions')
    answers = data.get('answers')
    key = data.get('key')
    if not questions or not answers or not key or not (len(questions) == len(answers) == len(key)):
        return jsonify({'success': False, 'error': 'Provide questions, answers, and key (all lists of same length)'}), 400
    # Use Gemini to grade and provide feedback
    prompt = (
        f"Grade the following student answers. For each question, compare the answer to the key, give a score (1 or 0), and provide a short feedback. "
        f"Return a JSON list with fields: question, answer, key, score, feedback.\n"
        f"Questions: {questions}\nAnswers: {answers}\nKey: {key}"
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        grading = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'grading': grading})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 13. Enhanced Translation: Real-time translation
@app.route('/translate', methods=['POST'])
def enhanced_translate():
    """Translate content/messages in real time."""
    data = request.json
    text = data.get('text')
    target_language = data.get('target_language')
    if not text or not target_language:
        return jsonify({'success': False, 'error': 'Provide text and target_language'}), 400
    # Use Gemini to translate (mock for now)
    prompt = f"Translate the following text to {target_language}:\n{text}"
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            prompt,
        ])
        translation = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'translation': translation, 'target_language': target_language})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 14. Code Evaluation: Code/practical generation and evaluation for UG/PG
@app.route('/code/evaluate', methods=['POST'])
def code_evaluate():
    """Generate and evaluate code/practicals for UG/PG levels."""
    # TODO: Integrate code evaluation APIs or use Gemini for code review/feedback
    return jsonify({'success': False, 'message': 'Not implemented yet'}), 501

# Gemini 2.0/2.5 Flash Advanced Features (using Google genai SDK)
@app.route('/gemini/url-context', methods=['POST'])
def gemini_url_context():
    """Fetch and summarize information from a web link using Gemini 2.5 Flash and url_context tool."""
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            url, "Summarize the main points of this web page for a teacher."
        ])
        summary = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/gemini/text-to-speech', methods=['POST'])
def gemini_text_to_speech():
    """Generate high quality speech from text using Gemini 2.5 Flash TTS."""
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")
        response = model.generate_content(text)
        data_audio = response.candidates[0].content.parts[0].inline_data.data if hasattr(response.candidates[0].content.parts[0], 'inline_data') else response.audio
        file_name = 'static/gemini_tts_out.wav'
        with wave.open(file_name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(data_audio)
        return send_file(file_name, mimetype='audio/wav', as_attachment=False)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/gemini/audio-dialog', methods=['POST'])
def gemini_audio_dialog():
    """Live audio-to-audio dialog with Gemini 2.5 Flash (mocked for now)."""
    # TODO: Implement real audio dialog with Gemini 2.5 Flash when API supports it
    try:
        response_text = "This is a mock Gemini dialog response."
        return jsonify({'success': True, 'response': response_text, 'audio_url': '/static/demo_audio.mp3'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/gemini/generate-image', methods=['POST'])
def gemini_generate_image():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'success': False, 'error': 'No prompt provided'}), 400
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")
        if types and hasattr(types, 'GenerateContentConfig'):
            config = types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
            response = model.generate_content(prompt, generation_config=config)
        else:
            config = {"response_modalities": ["TEXT", "IMAGE"]}
            response = model.generate_content(prompt, generation_config=config)
        image_b64 = None
        caption = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data is not None:
                mime_type = getattr(part.inline_data, 'mime_type', None)
                if mime_type and mime_type.startswith('image/'):
                    from PIL import Image
                    from io import BytesIO
                    import base64
                    try:
                        image = Image.open(BytesIO(part.inline_data.data))
                        buffered = BytesIO()
                        image.save(buffered, format="PNG")
                        image_b64 = base64.b64encode(buffered.getvalue()).decode()
                    except Exception:
                        # Not a valid image, skip
                        continue
            elif hasattr(part, 'text') and part.text is not None:
                caption = part.text
        return jsonify({'success': True, 'image': image_b64, 'caption': caption})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/wellbeing')
def wellbeing_page():
    return render_template('wellbeing.html')

@app.route('/feedback')
def feedback_page():
    return render_template('feedback.html')

@app.route('/social')
def social_page():
    return render_template('social.html')

@app.route('/timetable')
def timetable_page():
    return render_template('timetable.html')

@app.route('/peer')
def peer_page():
    return render_template('peer.html')

@app.route('/nep')
def nep_page():
    return render_template('nep.html')

@app.route('/co-teaching')
def co_teaching_page():
    return render_template('co_teaching.html')

@app.route('/behavior')
def behavior_page():
    return render_template('behavior.html')

@app.route('/parental')
def parental_page():
    return render_template('parental.html')

@app.route('/assessment')
def assessment_page():
    return render_template('assessment.html')

@app.route('/translate')
def translate_page():
    return render_template('translate.html')

@app.route('/code')
def code_page():
    return render_template('code.html')

@app.route('/image-gen')
def image_gen_page():
    return render_template('image_gen.html')

@app.route('/url-context')
def url_context_page():
    return render_template('url_context.html')

@app.route('/tts')
def tts_page():
    return render_template('tts.html')

@app.route('/audio-dialog')
def audio_dialog_page():
    return render_template('audio_dialog.html')

@app.route('/ai-agent')
def ai_agent_page():
    return render_template('ai_agent.html')

if __name__ == '__main__':
    app.run(debug=True, port=5007)
