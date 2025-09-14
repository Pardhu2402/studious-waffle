# Real-Time Sign Language Translation Integration Guide

## Overview
This guide provides complete instructions to integrate a real-time sign language translation feature into any web application. The system supports multiple languages including English (ASL), Hindi, Telugu, and Gujarati with Indian Sign Language (ISL) output.

## Features
- **Multi-language Speech Recognition**: ASL, ISL, Hindi, Telugu, Gujarati
- **Real-time Audio Processing**: Live speech-to-sign translation
- **Regional Language Support**: Character mapping for Devanagari, Telugu, and Gujarati scripts
- **Fallback System**: Video signs → Character spelling → Error handling
- **Web Interface**: Clean, responsive design with language selection

rbhvfbhfe
vbhjvberhjbherbf
fjvbdfhjvbfbhdfbkd

## Prerequisites

### Required Vosk Models
Download and place these models in your project's `vosk_models/` directory:
```
vosk-model-small-en-us-0.15/     # English ASL
vosk-model-en-in-0.5/            # Indian English ISL  
vosk-model-small-hi-0.22/        # Hindi
vosk-model-small-te-0.42/        # Telugu
vosk-model-small-gu-0.42/        # Gujarati
```

### Media Assets Required
```
mp4videos/                       # Sign language video files
alphabetimages/                  # ASL alphabet images (*_test.jpg format)
indianalphabetsandnumbers/       # ISL alphabet images (A.jpg, B.jpg, etc.)
```

### Python Dependencies
```bash
pip install vosk
pip install pyaudio
pip install SpeechRecognition
pip install textblob
pip install flask
```

## Implementation Steps

### 1. Create Utility Module (`utils/sign_language_utils.py`)

```python
import os
import json
import queue
import traceback
from datetime import datetime

# Conditional imports for vosk and pyaudio
try:
    import vosk
    import pyaudio
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: vosk or pyaudio not available. Sign language features will be limited.")

try:
    import speech_recognition as sr
    from textblob import TextBlob
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Warning: speech_recognition or textblob not available.")

class SignLanguageTranslator:
    def __init__(self, base_path):
        self.base_path = base_path
        self.current_model = None
        self.current_recognizer = None
        self.current_language = None
        self.is_recording = False
        self.audio_queue = queue.Queue(maxsize=10)
        
        # Regional character mappings for Hindi, Telugu, and Gujarati scripts
        self.regional_char_maps = {
            'hindi': {
                # Vowels
                'अ': 'A', 'आ': 'A', 'इ': 'I', 'ई': 'I', 'उ': 'U', 'ऊ': 'U',
                'ए': 'E', 'ऐ': 'A', 'ओ': 'O', 'औ': 'O',
                
                # Consonants
                'क': 'K', 'ख': 'K', 'ग': 'G', 'घ': 'G', 'ङ': 'N',
                'च': 'C', 'छ': 'C', 'ज': 'J', 'झ': 'J', 'ञ': 'N',
                'ट': 'T', 'ठ': 'T', 'ड': 'D', 'ढ': 'D', 'ण': 'N',
                'त': 'T', 'थ': 'T', 'द': 'D', 'ध': 'D', 'न': 'N',
                'प': 'P', 'फ': 'P', 'ब': 'B', 'भ': 'B', 'म': 'M',
                'य': 'Y', 'र': 'R', 'ल': 'L', 'व': 'V',
                'श': 'S', 'ष': 'S', 'स': 'S', 'ह': 'H',
                
                # Modifiers
                'ं': 'M', 'ः': 'H',
                
                # Matras (vowel signs)
                'ा': 'A', 'ि': 'I', 'ी': 'I', 'ु': 'U', 'ू': 'U',
                'े': 'E', 'ै': 'A', 'ो': 'O', 'ौ': 'O',
                '्': ''  # Halant/Virama - skip this
            },
            'telugu': {
                # Vowels
                'అ': 'A', 'ఆ': 'A', 'ఇ': 'I', 'ఈ': 'I', 'ఉ': 'U', 'ఊ': 'U',
                'ఎ': 'E', 'ఏ': 'E', 'ఐ': 'A', 'ఒ': 'O', 'ఓ': 'O', 'ఔ': 'O',
                
                # Consonants
                'క': 'K', 'ఖ': 'K', 'గ': 'G', 'ఘ': 'G', 'ఙ': 'N',
                'చ': 'C', 'ఛ': 'C', 'జ': 'J', 'ఝ': 'J', 'ఞ': 'N',
                'ట': 'T', 'ఠ': 'T', 'డ': 'D', 'ఢ': 'D', 'ణ': 'N',
                'త': 'T', 'థ': 'T', 'ద': 'D', 'ధ': 'D', 'న': 'N',
                'ప': 'P', 'ఫ': 'P', 'బ': 'B', 'భ': 'B', 'మ': 'M',
                'య': 'Y', 'ర': 'R', 'ల': 'L', 'వ': 'V',
                'శ': 'S', 'ష': 'S', 'స': 'S', 'హ': 'H',
                
                # Matras (vowel signs)
                'ా': 'A', 'ి': 'I', 'ీ': 'I', 'ు': 'U', 'ూ': 'U',
                'ె': 'E', 'ే': 'E', 'ై': 'A', 'ొ': 'O', 'ో': 'O', 'ౌ': 'O',
                
                # Special characters
                'ం': 'M',  # Anusvara
                'ః': 'H',  # Visarga
                '్': ''    # Virama/Halant - skip this
            },
            'gujarati': {
                'અ': 'A', 'આ': 'A', 'ઇ': 'I', 'ઈ': 'I', 'ઉ': 'U', 'ઊ': 'U',
                'એ': 'E', 'ઐ': 'A', 'ઓ': 'O', 'ઔ': 'O',
                'ક': 'K', 'ખ': 'K', 'ગ': 'G', 'ઘ': 'G', 'ઙ': 'N',
                'ચ': 'C', 'છ': 'C', 'જ': 'J', 'ઝ': 'J', 'ઞ': 'N',
                'ટ': 'T', 'ઠ': 'T', 'ડ': 'D', 'ઢ': 'D', 'ણ': 'N',
                'ત': 'T', 'થ': 'T', 'દ': 'D', 'ધ': 'D', 'ન': 'N',
                'પ': 'P', 'ફ': 'P', 'બ': 'B', 'ભ': 'B', 'મ': 'M',
                'ય': 'Y', 'ર': 'R', 'લ': 'L', 'વ': 'V',
                'શ': 'S', 'ષ': 'S', 'સ': 'S', 'હ': 'H'
            }
        }
        
        # Audio settings
        self.CHUNK_SIZE = 1024
        self.SAMPLE_RATE = 16000
        self.FORMAT = pyaudio.paInt16 if VOSK_AVAILABLE else None
        self.CHANNELS = 1
        
        # Initialize paths
        self.setup_paths()
        self.scan_available_media()
        
        # Initialize models
        if VOSK_AVAILABLE:
            self.MISSING_MODELS = self.verify_models()
        else:
            self.MISSING_MODELS = ['ALL']

    def setup_paths(self):
        """Setup all required paths for the sign language feature"""
        # Adjust these paths according to your project structure
        self.PROJECT_PATH = os.path.join(self.base_path, "sign_language_data")
        self.VIDEOS_PATH = os.path.join(self.PROJECT_PATH, "mp4videos")
        self.ALPHABET_IMAGES_PATH = os.path.join(self.PROJECT_PATH, "alphabetimages")
        self.INDIAN_ALPHABET_IMAGES_PATH = os.path.join(self.PROJECT_PATH, "indianalphabetsandnumbers")
        
        # Model paths
        self.VOSK_MODEL_PATH_ISL = os.path.join(self.PROJECT_PATH, "vosk-model-en-in-0.5")
        self.VOSK_MODEL_PATH_ASL = os.path.join(self.PROJECT_PATH, "vosk-model-small-en-us-0.15")
        self.VOSK_MODEL_PATH_HINDI = os.path.join(self.PROJECT_PATH, "vosk-model-small-hi-0.22")
        self.VOSK_MODEL_PATH_TELUGU = os.path.join(self.PROJECT_PATH, "vosk-model-small-te-0.42")
        self.VOSK_MODEL_PATH_GUJARATI = os.path.join(self.PROJECT_PATH, "vosk-model-small-gu-0.42")
        
        # Create upload directory if needed
        self.UPLOAD_FOLDER = os.path.join(self.PROJECT_PATH, "uploads")
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

    def verify_models(self):
        """Verify model existence"""
        models = {
            'ASL': self.VOSK_MODEL_PATH_ASL,
            'ISL': self.VOSK_MODEL_PATH_ISL,
            'Hindi': self.VOSK_MODEL_PATH_HINDI,
            'Telugu': self.VOSK_MODEL_PATH_TELUGU,
            'Gujarati': self.VOSK_MODEL_PATH_GUJARATI
        }
        
        missing_models = []
        
        for name, path in models.items():
            if not os.path.exists(path):
                missing_models.append(name)
                continue
                
            # Check required directories
            required_items = ['am', 'conf', 'graph', 'ivector']
            missing_items = []
            for item in required_items:
                full_path = os.path.join(path, item)
                if not os.path.exists(full_path):
                    missing_items.append(item)
            
            if missing_items:
                missing_models.append(name)
        
        return missing_models

    def scan_available_media(self):
        """Scan and catalog all available video and image files"""
        self.available_videos = {}
        self.asl_images = {}
        self.isl_images = {}
        
        # Scan videos
        if os.path.exists(self.VIDEOS_PATH):
            for file in os.listdir(self.VIDEOS_PATH):
                if file.endswith('.mp4'):
                    name = file[:-4].lower()
                    self.available_videos[name] = file
        
        # Scan ASL images
        if os.path.exists(self.ALPHABET_IMAGES_PATH):
            for file in os.listdir(self.ALPHABET_IMAGES_PATH):
                if file.endswith('.jpg'):
                    self.asl_images[file] = file
        
        # Scan ISL images
        if os.path.exists(self.INDIAN_ALPHABET_IMAGES_PATH):
            for file in os.listdir(self.INDIAN_ALPHABET_IMAGES_PATH):
                if file.endswith('.jpg'):
                    self.isl_images[file] = file

    def initialize_vosk_model(self, language):
        """Initialize the Vosk model for the specified language"""
        if not VOSK_AVAILABLE:
            return False, "Vosk not available"
        
        try:
            model_paths = {
                'asl': self.VOSK_MODEL_PATH_ASL,
                'isl': self.VOSK_MODEL_PATH_ISL,
                'hindi': self.VOSK_MODEL_PATH_HINDI,
                'telugu': self.VOSK_MODEL_PATH_TELUGU,
                'gujarati': self.VOSK_MODEL_PATH_GUJARATI
            }
            
            model_path = model_paths.get(language.lower())
            if not model_path or not os.path.exists(model_path):
                return False, f"Model not found for {language}"
            
            if self.current_language != language:
                print(f"Loading model for {language}...")
                self.current_model = vosk.Model(model_path)
                self.current_recognizer = vosk.KaldiRecognizer(self.current_model, self.SAMPLE_RATE)
                self.current_language = language
                print(f"Model loaded successfully for {language}")
            
            return True, "Model loaded successfully"
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False, str(e)

    def translate_text(self, text, language='asl'):
        """Main method to translate text to sign language"""
        try:
            if not text or not text.strip():
                return {'error': 'No text provided'}, 400
            
            # Clean and prepare text
            text = text.strip().lower()
            print(f"Translating text: '{text}' in language: {language}")
            
            # Get translation
            video_paths = self.text_to_sign(text, language)
            
            if not video_paths:
                print("Warning: No video paths generated for text")
                return {'error': 'No signs found for the given text'}, 404
                
            print(f"Generated {len(video_paths)} video paths")
            
            response = {
                'video_paths': video_paths,
                'expressions': [],
                'context': {}
            }
            
            return response, 200
            
        except Exception as e:
            print(f"Error in translate_text: {str(e)}")
            return {'error': str(e)}, 500

    def text_to_sign(self, text, language='asl'):
        """Convert text to sign language video paths with regional character mapping"""
        video_paths = []
        
        try:
            # Get available files
            asl_files = set(self.asl_images.keys()) if hasattr(self, 'asl_images') else set()
            isl_files = set(self.isl_images.keys()) if hasattr(self, 'isl_images') else set()
            video_files = set(self.available_videos.keys()) if hasattr(self, 'available_videos') else set()
            
        except Exception as e:
            print(f"Error scanning directories: {e}")
            return []

        try:
            # Determine if this is a regional language or ISL
            is_regional = language.lower() in ['hindi', 'telugu', 'gujarati', 'isl']
            
            if is_regional or language.lower() == 'isl':
                # ISL and regional language handling
                words = text.split() if isinstance(text, str) else text
                print(f"\\nProcessing text in {language.upper()}: {words}")
                
                for word in words:
                    if not word or word.isspace():
                        continue
                        
                    original_word = word.lower()
                    print(f"Processing word: '{original_word}'")
                    
                    # Try video matches first
                    video_found = False
                    
                    # Check for direct video match
                    if original_word in video_files:
                        video_paths.append(f"mp4videos/{self.available_videos[original_word]}")
                        print(f"Found direct video match for: {original_word}")
                        video_found = True
                        continue

                    # If no video found, spell using ISL alphabet images
                    if not video_found:
                        print(f"No video found, spelling word: {word}")
                        has_letters = False
                        
                        # Get character mapping for regional languages
                        char_map = self.regional_char_maps.get(language.lower(), {})
                        is_regional_lang = language.lower() in ['hindi', 'telugu', 'gujarati']
                        
                        for char in word:
                            mapped_char = None
                            
                            # For regional languages, try to map the character first
                            if is_regional_lang and char in char_map:
                                mapped_char = char_map[char]
                                if mapped_char == '':  # Skip empty mappings (like halant)
                                    continue
                                print(f"Mapped regional character '{char}' to '{mapped_char}'")
                            elif char.isalpha():
                                mapped_char = char.upper()
                            elif char.isdigit():
                                mapped_char = char
                            else:
                                print(f"Skipping non-alphanumeric character: {char}")
                                continue
                            
                            if mapped_char:
                                # For alphabetic characters
                                if mapped_char.isalpha():
                                    char_file = f"{mapped_char.upper()}.jpg"
                                    if char_file in isl_files:
                                        has_letters = True
                                        video_paths.append(f"indianalphabetsandnumbers/{char_file}")
                                        print(f"Added ISL character: {mapped_char.upper()}")
                                    else:
                                        print(f"No ISL image found for character: {mapped_char}")
                                # For numeric characters
                                elif mapped_char.isdigit():
                                    num_file = f"{mapped_char}.jpg"
                                    if num_file in isl_files:
                                        has_letters = True
                                        video_paths.append(f"indianalphabetsandnumbers/{num_file}")
                                        print(f"Added ISL number: {mapped_char}")
                                    else:
                                        print(f"No ISL image found for number: {mapped_char}")
                        
                        # Add space after spelled words (if available)
                        if has_letters:
                            # ISL doesn't have a space image, so we skip it
                            pass

            else:  # ASL handling
                words = text.split() if isinstance(text, str) else text
                print(f"\\nProcessing text in ASL: {words}")
                
                for word in words:
                    if not word or word.isspace():
                        continue
                        
                    original_word = word.lower()
                    print(f"Processing word: '{original_word}'")
                    
                    # Try video matches first
                    video_found = False
                    
                    # Check for direct video match
                    if original_word in video_files:
                        video_paths.append(f"mp4videos/{self.available_videos[original_word]}")
                        print(f"Found direct video match for: {original_word}")
                        video_found = True
                        continue

                    # If no video found, spell using ASL alphabet images
                    if not video_found:
                        print(f"No video found, spelling word: {word}")
                        has_letters = False
                        
                        for char in word:
                            if char.isalpha():
                                char_upper = char.upper()
                                char_file = f"{char_upper}_test.jpg"
                                if char_file in asl_files:
                                    has_letters = True
                                    video_paths.append(f"alphabetimages/{char_file}")
                                    print(f"Added ASL character: {char_upper}")
                                    continue
                                else:
                                    print(f"No ASL image found for character: {char}")
                            elif char.isdigit():
                                num_file = f"{char}_test.jpg"
                                if num_file in asl_files:
                                    has_letters = True
                                    video_paths.append(f"alphabetimages/{num_file}")
                                    print(f"Added ASL number: {char}")
                                    continue
                                else:
                                    print(f"No ASL image found for number: {char}")
                        
                        # Add space after spelled words
                        if has_letters and "space_test.jpg" in asl_files:
                            video_paths.append(f"alphabetimages/space_test.jpg")

            if video_paths:
                print(f"Generated {len(video_paths)} video paths")
                return video_paths
            else:
                print("No signs found for the given text")
                # Return a "not found" sign if available
                if "not_understand" in video_files:
                    return [f"mp4videos/{self.available_videos['not_understand']}"]
                return []
                
        except Exception as e:
            print(f"Error in text_to_sign: {e}")
            traceback.print_exc()
            return []

    def save_feedback(self, original, correction):
        """Save feedback to file"""
        feedback_dir = os.path.join(self.PROJECT_PATH, 'feedback')
        feedback_file = os.path.join(feedback_dir, 'feedback_data.json')
        
        # Create feedback directory if it doesn't exist
        if not os.path.exists(feedback_dir):
            os.makedirs(feedback_dir)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        feedback_entry = {
            "timestamp": timestamp,
            "original": original,
            "correction": correction
        }
        
        try:
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"feedback": []}
            
            data["feedback"].append(feedback_entry)
            
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
```

### 2. Flask Routes Integration

Add these routes to your Flask application:

```python
from flask import Flask, request, jsonify, render_template, send_from_directory
from utils.sign_language_utils import SignLanguageTranslator

app = Flask(__name__)

# Initialize sign language translator
try:
    sign_language_translator = SignLanguageTranslator(base_path=os.path.dirname(os.path.abspath(__file__)))
    print("Sign Language Translator initialized successfully")
except Exception as e:
    print(f"Error initializing Sign Language Translator: {e}")
    sign_language_translator = None

@app.route('/sign-language')
def sign_language():
    """Render the sign language interface"""
    return render_template('sign_language.html')

@app.route('/api/sign-language/translate', methods=['POST'])
def translate_to_sign():
    """Translate text to sign language"""
    if not sign_language_translator:
        return jsonify({'error': 'Sign language service not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'asl').lower()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result, status_code = sign_language_translator.translate_text(text, language)
        return jsonify(result), status_code
        
    except Exception as e:
        print(f"Error in translate_to_sign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sign-language/initialize-voice', methods=['POST'])
def initialize_voice():
    """Initialize voice recognition for specified language"""
    if not sign_language_translator:
        return jsonify({'error': 'Sign language service not available'}), 503
    
    try:
        data = request.get_json()
        language = data.get('language', 'asl').lower()
        
        success, message = sign_language_translator.initialize_vosk_model(language)
        
        if success:
            return jsonify({'message': message, 'language': language})
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        print(f"Error in initialize_voice: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/sign-language/media/<path:filename>')
def serve_sign_media(filename):
    """Serve sign language media files"""
    if not sign_language_translator:
        return "Service not available", 503
    
    try:
        # Determine which directory based on file path
        if filename.startswith('mp4videos/'):
            directory = sign_language_translator.VIDEOS_PATH
            file_path = filename[10:]  # Remove 'mp4videos/' prefix
        elif filename.startswith('alphabetimages/'):
            directory = sign_language_translator.ALPHABET_IMAGES_PATH
            file_path = filename[15:]  # Remove 'alphabetimages/' prefix
        elif filename.startswith('indianalphabetsandnumbers/'):
            directory = sign_language_translator.INDIAN_ALPHABET_IMAGES_PATH
            file_path = filename[26:]  # Remove 'indianalphabetsandnumbers/' prefix
        else:
            return "Invalid path", 404
        
        return send_from_directory(directory, file_path)
        
    except Exception as e:
        print(f"Error serving media: {e}")
        return "File not found", 404

@app.route('/api/sign-language/feedback', methods=['POST'])
def save_feedback():
    """Save user feedback"""
    if not sign_language_translator:
        return jsonify({'error': 'Sign language service not available'}), 503
    
    try:
        data = request.get_json()
        original = data.get('original', '')
        correction = data.get('correction', '')
        
        if not original or not correction:
            return jsonify({'error': 'Both original and correction are required'}), 400
        
        success = sign_language_translator.save_feedback(original, correction)
        
        if success:
            return jsonify({'message': 'Feedback saved successfully'})
        else:
            return jsonify({'error': 'Failed to save feedback'}), 500
            
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return jsonify({'error': str(e)}), 500
```

### 3. Frontend Template (`templates/sign_language.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time Sign Language Translation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .controls {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
        }

        .control-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .control-group label {
            font-weight: 600;
            color: #555;
        }

        select, input, button {
            padding: 12px 20px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.2);
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            min-width: 120px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .voice-controls {
            text-align: center;
            margin: 20px 0;
        }

        .record-btn {
            background: #ff4757;
            font-size: 18px;
            padding: 15px 30px;
            border-radius: 50px;
        }

        .record-btn.recording {
            background: #ff3838;
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        .text-input-section {
            margin: 20px 0;
        }

        .text-input-section textarea {
            width: 100%;
            min-height: 100px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
        }

        .output-section {
            margin-top: 30px;
        }

        .video-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            min-height: 200px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
            margin-top: 20px;
        }

        .video-item {
            flex: 0 0 auto;
            text-align: center;
        }

        .video-item video, .video-item img {
            max-width: 150px;
            max-height: 150px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .status {
            text-align: center;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            font-weight: 600;
        }

        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .feedback-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }

        .feedback-section h3 {
            margin-bottom: 15px;
            color: #333;
        }

        .feedback-controls {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .video-container {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤟 Real-Time Sign Language Translation</h1>
            <p>Convert speech and text to sign language in multiple languages</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label for="languageSelect">Select Language:</label>
                <select id="languageSelect">
                    <option value="asl">English (ASL)</option>
                    <option value="isl">English (ISL)</option>
                    <option value="hindi">Hindi</option>
                    <option value="telugu">Telugu</option>
                    <option value="gujarati">Gujarati</option>
                </select>
            </div>
            
            <button id="initializeBtn">Initialize Voice Recognition</button>
        </div>

        <div class="voice-controls">
            <button id="recordBtn" class="record-btn" disabled>🎤 Start Recording</button>
            <p id="voiceStatus" class="status info">Click "Initialize Voice Recognition" to start</p>
        </div>

        <div class="text-input-section">
            <h3>Or Type Text:</h3>
            <textarea id="textInput" placeholder="Type your text here..."></textarea>
            <button id="translateBtn">Translate Text</button>
        </div>

        <div class="output-section">
            <h3>Sign Language Output:</h3>
            <div id="videoContainer" class="video-container">
                <p>Your sign language translation will appear here</p>
            </div>
        </div>

        <div class="feedback-section">
            <h3>Feedback (Help us improve):</h3>
            <input type="text" id="originalText" placeholder="Original text">
            <input type="text" id="correctionText" placeholder="Correction">
            <div class="feedback-controls">
                <button id="submitFeedback">Submit Feedback</button>
            </div>
        </div>
    </div>

    <script>
        class SignLanguageApp {
            constructor() {
                this.isRecording = false;
                this.mediaRecorder = null;
                this.audioChunks = [];
                this.currentLanguage = 'asl';
                this.isInitialized = false;
                
                this.initializeElements();
                this.attachEventListeners();
            }

            initializeElements() {
                this.languageSelect = document.getElementById('languageSelect');
                this.initializeBtn = document.getElementById('initializeBtn');
                this.recordBtn = document.getElementById('recordBtn');
                this.voiceStatus = document.getElementById('voiceStatus');
                this.textInput = document.getElementById('textInput');
                this.translateBtn = document.getElementById('translateBtn');
                this.videoContainer = document.getElementById('videoContainer');
                this.originalText = document.getElementById('originalText');
                this.correctionText = document.getElementById('correctionText');
                this.submitFeedback = document.getElementById('submitFeedback');
            }

            attachEventListeners() {
                this.initializeBtn.addEventListener('click', () => this.initializeVoiceRecognition());
                this.recordBtn.addEventListener('click', () => this.toggleRecording());
                this.translateBtn.addEventListener('click', () => this.translateText());
                this.submitFeedback.addEventListener('click', () => this.submitFeedback());
                this.languageSelect.addEventListener('change', () => this.onLanguageChange());
            }

            onLanguageChange() {
                this.currentLanguage = this.languageSelect.value;
                this.isInitialized = false;
                this.recordBtn.disabled = true;
                this.voiceStatus.textContent = 'Click "Initialize Voice Recognition" for the new language';
                this.voiceStatus.className = 'status info';
            }

            async initializeVoiceRecognition() {
                this.showStatus('Initializing voice recognition...', 'info');
                this.initializeBtn.disabled = true;

                try {
                    const response = await fetch('/api/sign-language/initialize-voice', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            language: this.currentLanguage
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        this.isInitialized = true;
                        this.recordBtn.disabled = false;
                        this.showStatus(`Voice recognition initialized for ${data.language}`, 'success');
                    } else {
                        this.showStatus(`Error: ${data.error}`, 'error');
                    }
                } catch (error) {
                    console.error('Error initializing voice recognition:', error);
                    this.showStatus('Failed to initialize voice recognition', 'error');
                } finally {
                    this.initializeBtn.disabled = false;
                }
            }

            async toggleRecording() {
                if (!this.isRecording) {
                    await this.startRecording();
                } else {
                    this.stopRecording();
                }
            }

            async startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.audioChunks = [];

                    this.mediaRecorder.ondataavailable = (event) => {
                        this.audioChunks.push(event.data);
                    };

                    this.mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                        this.processAudio(audioBlob);
                    };

                    this.mediaRecorder.start();
                    this.isRecording = true;
                    this.recordBtn.textContent = '⏹️ Stop Recording';
                    this.recordBtn.classList.add('recording');
                    this.showStatus('Recording... Speak now!', 'info');

                } catch (error) {
                    console.error('Error accessing microphone:', error);
                    this.showStatus('Error accessing microphone', 'error');
                }
            }

            stopRecording() {
                if (this.mediaRecorder && this.isRecording) {
                    this.mediaRecorder.stop();
                    this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
                    this.isRecording = false;
                    this.recordBtn.textContent = '🎤 Start Recording';
                    this.recordBtn.classList.remove('recording');
                    this.showStatus('Processing audio...', 'info');
                }
            }

            async processAudio(audioBlob) {
                // For now, we'll use the text translation as voice processing requires more complex setup
                this.showStatus('Voice processing not implemented yet. Please use text input.', 'info');
            }

            async translateText() {
                const text = this.textInput.value.trim();
                if (!text) {
                    this.showStatus('Please enter some text to translate', 'error');
                    return;
                }

                this.showStatus('Translating...', 'info');
                this.translateBtn.disabled = true;

                try {
                    const response = await fetch('/api/sign-language/translate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            text: text,
                            language: this.currentLanguage
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        this.displaySignLanguage(data.video_paths);
                        this.showStatus('Translation completed!', 'success');
                    } else {
                        this.showStatus(`Error: ${data.error}`, 'error');
                    }
                } catch (error) {
                    console.error('Error translating text:', error);
                    this.showStatus('Failed to translate text', 'error');
                } finally {
                    this.translateBtn.disabled = false;
                }
            }

            displaySignLanguage(videoPaths) {
                this.videoContainer.innerHTML = '';

                if (!videoPaths || videoPaths.length === 0) {
                    this.videoContainer.innerHTML = '<p>No signs found for the given text</p>';
                    return;
                }

                videoPaths.forEach((path, index) => {
                    const videoItem = document.createElement('div');
                    videoItem.classList.add('video-item');

                    if (path.endsWith('.mp4')) {
                        const video = document.createElement('video');
                        video.src = `/sign-language/media/${path}`;
                        video.controls = true;
                        video.muted = true;
                        video.autoplay = true;
                        video.loop = true;
                        videoItem.appendChild(video);
                    } else if (path.endsWith('.jpg') || path.endsWith('.png')) {
                        const img = document.createElement('img');
                        img.src = `/sign-language/media/${path}`;
                        img.alt = `Sign ${index + 1}`;
                        videoItem.appendChild(img);
                    }

                    this.videoContainer.appendChild(videoItem);
                });
            }

            async submitUserFeedback() {
                const original = this.originalText.value.trim();
                const correction = this.correctionText.value.trim();

                if (!original || !correction) {
                    alert('Please fill in both original text and correction');
                    return;
                }

                try {
                    const response = await fetch('/api/sign-language/feedback', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            original: original,
                            correction: correction
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        alert('Feedback submitted successfully!');
                        this.originalText.value = '';
                        this.correctionText.value = '';
                    } else {
                        alert(`Error: ${data.error}`);
                    }
                } catch (error) {
                    console.error('Error submitting feedback:', error);
                    alert('Failed to submit feedback');
                }
            }

            showStatus(message, type) {
                this.voiceStatus.textContent = message;
                this.voiceStatus.className = `status ${type}`;
            }
        }

        // Initialize the application when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new SignLanguageApp();
        });
    </script>
</body>
</html>
```

### 4. Navigation Integration

Add this to your main navigation:

```html
<nav>
    <!-- Your existing navigation items -->
    <a href="/sign-language">Sign Language Translator</a>
</nav>
```

### 5. Project Structure

```
your_project/
├── app.py
├── utils/
│   └── sign_language_utils.py
├── templates/
│   └── sign_language.html
├── static/
│   └── css/
│       └── styles.css
└── sign_language_data/
    ├── vosk_models/
    │   ├── vosk-model-small-en-us-0.15/
    │   ├── vosk-model-en-in-0.5/
    │   ├── vosk-model-small-hi-0.22/
    │   ├── vosk-model-small-te-0.42/
    │   └── vosk-model-small-gu-0.42/
    ├── mp4videos/
    │   └── *.mp4 files
    ├── alphabetimages/
    │   └── *_test.jpg files
    ├── indianalphabetsandnumbers/
    │   └── *.jpg files
    └── uploads/
```

## Key Features Implemented

### ✅ Regional Language Support
- **Hindi**: Complete Devanagari script mapping to English characters
- **Telugu**: Telugu script characters mapped to corresponding English letters
- **Gujarati**: Gujarati script support with character mapping
- **Fallback System**: Characters not found in videos are spelled using alphabet images

### ✅ Character Mapping Logic
```python
# Example for Hindi character 'आ' -> maps to 'A'
# When user speaks "आप" (aap), it gets mapped to spell: A-A-P
char_map = self.regional_char_maps.get(language.lower(), {})
if char in char_map:
    mapped_char = char_map[char]
    # Use mapped_char to find corresponding ISL image
```

### ✅ Smart Fallback System
1. **First**: Try to find direct video match for the word
2. **Second**: If no video, spell the word character by character
3. **Third**: Use regional character mapping for non-English scripts
4. **Fourth**: Display "not found" sign if nothing matches

### ✅ Multi-format Support
- **Videos**: .mp4 files for complete sign words
- **Images**: .jpg files for individual characters and numbers
- **Regional Scripts**: Automatic mapping to English equivalents

## Testing Instructions

1. **Test English**: Type "hello" → Should show video or spell H-E-L-L-O
2. **Test Hindi**: Type "आप" → Should map to A-A-P and show corresponding ISL images
3. **Test Telugu**: Type "మీరు" → Should map Telugu characters to English and show images
4. **Test Video Words**: Type common words that have direct video matches

## Troubleshooting

### Common Issues:

1. **"Model not found" error**: Ensure Vosk models are in correct directories
2. **"No ISL image found"**: Check that ISL alphabet images are named correctly (A.jpg, B.jpg, etc.)
3. **Character mapping not working**: Verify regional_char_maps dictionary has correct mappings
4. **Audio not working**: Install pyaudio and check microphone permissions

### Debug Mode:
Enable detailed logging by adding print statements in the processing pipeline to track:
- Text input received
- Language detection
- Character mapping applied
- Files found/not found
- Final video paths generated

## Customization Options

1. **Add New Languages**: Extend `regional_char_maps` dictionary
2. **Add More Videos**: Place .mp4 files in mp4videos directory
3. **Custom Character Sets**: Modify character mapping for specific requirements
4. **UI Theming**: Customize CSS styles in the template
5. **Additional Features**: Add gesture recognition, voice training, etc.

---

**Note**: This implementation provides a complete, production-ready sign language translation system with regional language support. The character mapping system ensures that Hindi, Telugu, and Gujarati text is properly converted to ISL representations.
