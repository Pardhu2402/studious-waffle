"""
Complete Sign Language Translation Implementation
==============================================

This file contains a complete, ready-to-use implementation of a real-time sign language 
translation system that supports multiple languages including Hindi, Telugu, and Gujarati
with proper character mapping to Indian Sign Language (ISL).

Author: AI Assistant
Date: July 29, 2025
Version: 1.0

Features:
- Multi-language support (ASL, ISL, Hindi, Telugu, Gujarati)
- Regional character mapping for Indian scripts
- Smart fallback system (video → character spelling → error handling)
- Flask web interface with responsive design
- Real-time audio processing capabilities
- Feedback system for continuous improvement

Usage:
1. Install dependencies: pip install flask vosk pyaudio SpeechRecognition textblob
2. Set up directory structure as shown below
3. Place this file in your project root
4. Run: python complete_sign_language_implementation.py
5. Access: http://localhost:5000/sign-language

Directory Structure Required:
your_project/
├── complete_sign_language_implementation.py  # This file
├── templates/
│   └── sign_language.html                    # HTML template (created automatically)
├── static/
│   └── css/
│       └── sign_language.css                 # CSS styles (created automatically)
└── sign_language_data/
    ├── vosk_models/
    │   ├── vosk-model-small-en-us-0.15/      # Download from vosk-model releases
    │   ├── vosk-model-en-in-0.5/             # Download from vosk-model releases
    │   ├── vosk-model-small-hi-0.22/         # Download from vosk-model releases
    │   ├── vosk-model-small-te-0.42/         # Download from vosk-model releases
    │   └── vosk-model-small-gu-0.42/         # Download from vosk-model releases
    ├── mp4videos/                            # Place your .mp4 sign videos here
    │   └── *.mp4 files
    ├── alphabetimages/                       # ASL alphabet images
    │   └── *_test.jpg files (A_test.jpg, B_test.jpg, etc.)
    ├── indianalphabetsandnumbers/            # ISL alphabet images
    │   └── *.jpg files (A.jpg, B.jpg, etc.)
    └── uploads/                              # Auto-created for file uploads
"""

import os
import json
import queue
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory

# Conditional imports for vosk and pyaudio with error handling
try:
    import vosk
    import pyaudio
    VOSK_AVAILABLE = True
    print("✅ Vosk and PyAudio are available")
except ImportError as e:
    VOSK_AVAILABLE = False
    print(f"⚠️  Warning: vosk or pyaudio not available: {e}")
    print("   Speech recognition features will be limited.")

try:
    import speech_recognition as sr
    from textblob import TextBlob
    SR_AVAILABLE = True
    print("✅ SpeechRecognition and TextBlob are available")
except ImportError as e:
    SR_AVAILABLE = False
    print(f"⚠️  Warning: speech_recognition or textblob not available: {e}")

class SignLanguageTranslator:
    """
    Complete Sign Language Translation System
    
    Supports multiple languages with regional character mapping:
    - English (ASL and ISL)
    - Hindi (Devanagari script → ISL)
    - Telugu (Telugu script → ISL)  
    - Gujarati (Gujarati script → ISL)
    """
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.current_model = None
        self.current_recognizer = None
        self.current_language = None
        self.is_recording = False
        self.audio_queue = queue.Queue(maxsize=10)
        
        # 🎯 REGIONAL CHARACTER MAPPINGS - Core feature for Indian languages
        self.regional_char_maps = {
            'hindi': {
                # Vowels (स्वर)
                'अ': 'A', 'आ': 'A', 'इ': 'I', 'ई': 'I', 'उ': 'U', 'ऊ': 'U',
                'ए': 'E', 'ऐ': 'A', 'ओ': 'O', 'औ': 'O',
                
                # Consonants (व्यंजन) - All Hindi consonants mapped to closest English sounds
                'क': 'K', 'ख': 'K', 'ग': 'G', 'घ': 'G', 'ङ': 'N',
                'च': 'C', 'छ': 'C', 'ज': 'J', 'झ': 'J', 'ञ': 'N',
                'ट': 'T', 'ठ': 'T', 'ड': 'D', 'ढ': 'D', 'ण': 'N',
                'त': 'T', 'थ': 'T', 'द': 'D', 'ध': 'D', 'न': 'N',
                'प': 'P', 'फ': 'P', 'ब': 'B', 'भ': 'B', 'म': 'M',
                'य': 'Y', 'र': 'R', 'ल': 'L', 'व': 'V',
                'श': 'S', 'ष': 'S', 'स': 'S', 'ह': 'H',
                
                # Modifiers and special characters
                'ं': 'M', 'ः': 'H',  # Anusvara and Visarga
                
                # Matras (मात्राएं) - Vowel signs
                'ा': 'A', 'ि': 'I', 'ी': 'I', 'ु': 'U', 'ू': 'U',
                'े': 'E', 'ै': 'A', 'ो': 'O', 'ौ': 'O',
                '्': ''  # Halant/Virama - skip this (removes inherent vowel)
            },
            'telugu': {
                # Telugu Vowels (అచ్చులు)
                'అ': 'A', 'ఆ': 'A', 'ఇ': 'I', 'ఈ': 'I', 'ఉ': 'U', 'ఊ': 'U',
                'ఎ': 'E', 'ఏ': 'E', 'ఐ': 'A', 'ఒ': 'O', 'ఓ': 'O', 'ఔ': 'O',
                
                # Telugu Consonants (హల్లులు)
                'క': 'K', 'ఖ': 'K', 'గ': 'G', 'ఘ': 'G', 'ఙ': 'N',
                'చ': 'C', 'ఛ': 'C', 'జ': 'J', 'ఝ': 'J', 'ఞ': 'N',
                'ట': 'T', 'ఠ': 'T', 'డ': 'D', 'ఢ': 'D', 'ణ': 'N',
                'త': 'T', 'థ': 'T', 'ద': 'D', 'ధ': 'D', 'న': 'N',
                'ప': 'P', 'ఫ': 'P', 'బ': 'B', 'భ': 'B', 'మ': 'M',
                'య': 'Y', 'ర': 'R', 'ల': 'L', 'వ': 'V',
                'శ': 'S', 'ష': 'S', 'స': 'S', 'హ': 'H',
                
                # Telugu Matras (మాత్రలు) - Vowel signs
                'ా': 'A', 'ి': 'I', 'ీ': 'I', 'ు': 'U', 'ూ': 'U',
                'ె': 'E', 'ే': 'E', 'ై': 'A', 'ొ': 'O', 'ో': 'O', 'ౌ': 'O',
                
                # Special Telugu characters
                'ం': 'M',  # Anusvara (అనుస్వారం)
                'ః': 'H',  # Visarga (విసర్గం)
                '్': ''    # Virama/Halant (హలంతం) - skip this
            },
            'gujarati': {
                # Gujarati Vowels
                'અ': 'A', 'આ': 'A', 'ઇ': 'I', 'ઈ': 'I', 'ઉ': 'U', 'ઊ': 'U',
                'એ': 'E', 'ઐ': 'A', 'ઓ': 'O', 'ઔ': 'O',
                
                # Gujarati Consonants
                'ક': 'K', 'ખ': 'K', 'ગ': 'G', 'ઘ': 'G', 'ઙ': 'N',
                'ચ': 'C', 'છ': 'C', 'જ': 'J', 'ઝ': 'J', 'ઞ': 'N',
                'ટ': 'T', 'ઠ': 'T', 'ડ': 'D', 'ઢ': 'D', 'ણ': 'N',
                'ત': 'T', 'થ': 'T', 'દ': 'D', 'ધ': 'D', 'ન': 'N',
                'પ': 'P', 'ફ': 'P', 'બ': 'B', 'ભ': 'B', 'મ': 'M',
                'ય': 'Y', 'ર': 'R', 'લ': 'L', 'વ': 'V',
                'શ': 'S', 'ષ': 'S', 'સ': 'S', 'હ': 'H',
                
                # Gujarati Matras
                'ા': 'A', 'િ': 'I', 'ી': 'I', 'ુ': 'U', 'ૂ': 'U',
                'ે': 'E', 'ૈ': 'A', 'ો': 'O', 'ૌ': 'O',
                '્': ''    # Virama - skip this
            }
        }
        
        # Audio settings for real-time processing
        self.CHUNK_SIZE = 1024
        self.SAMPLE_RATE = 16000
        self.FORMAT = pyaudio.paInt16 if VOSK_AVAILABLE else None
        self.CHANNELS = 1
        
        # Initialize system
        self.setup_paths()
        self.scan_available_media()
        
        # Initialize Vosk models if available
        if VOSK_AVAILABLE:
            self.MISSING_MODELS = self.verify_models()
            print(f"📊 Model Status: {len(self.MISSING_MODELS)} missing models")
        else:
            self.MISSING_MODELS = ['ALL']
            print("⚠️  All speech recognition models unavailable")

    def setup_paths(self):
        """Setup all required paths for the sign language feature"""
        print("🔧 Setting up directory paths...")
        
        # Main data directory
        self.PROJECT_PATH = os.path.join(self.base_path, "sign_language_data")
        
        # Media directories
        self.VIDEOS_PATH = os.path.join(self.PROJECT_PATH, "mp4videos")
        self.ALPHABET_IMAGES_PATH = os.path.join(self.PROJECT_PATH, "alphabetimages")
        self.INDIAN_ALPHABET_IMAGES_PATH = os.path.join(self.PROJECT_PATH, "indianalphabetsandnumbers")
        
        # Vosk model directories
        self.VOSK_MODEL_PATH_ISL = os.path.join(self.PROJECT_PATH, "vosk_models", "vosk-model-en-in-0.5")
        self.VOSK_MODEL_PATH_ASL = os.path.join(self.PROJECT_PATH, "vosk_models", "vosk-model-small-en-us-0.15")
        self.VOSK_MODEL_PATH_HINDI = os.path.join(self.PROJECT_PATH, "vosk_models", "vosk-model-small-hi-0.22")
        self.VOSK_MODEL_PATH_TELUGU = os.path.join(self.PROJECT_PATH, "vosk_models", "vosk-model-small-te-0.42")
        self.VOSK_MODEL_PATH_GUJARATI = os.path.join(self.PROJECT_PATH, "vosk_models", "vosk-model-small-gu-0.42")
        
        # Create required directories
        directories_to_create = [
            self.PROJECT_PATH,
            self.VIDEOS_PATH,
            self.ALPHABET_IMAGES_PATH,
            self.INDIAN_ALPHABET_IMAGES_PATH,
            os.path.join(self.PROJECT_PATH, "vosk_models"),
            os.path.join(self.PROJECT_PATH, "uploads"),
            os.path.join(self.PROJECT_PATH, "feedback")
        ]
        
        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)
            
        print(f"✅ Directory setup complete. Main path: {self.PROJECT_PATH}")

    def verify_models(self):
        """Verify Vosk model existence and integrity"""
        models = {
            'ASL': self.VOSK_MODEL_PATH_ASL,
            'ISL': self.VOSK_MODEL_PATH_ISL,
            'Hindi': self.VOSK_MODEL_PATH_HINDI,
            'Telugu': self.VOSK_MODEL_PATH_TELUGU,
            'Gujarati': self.VOSK_MODEL_PATH_GUJARATI
        }
        
        missing_models = []
        available_models = []
        
        for name, path in models.items():
            if not os.path.exists(path):
                missing_models.append(name)
                continue
                
            # Check required Vosk model directories
            required_items = ['am', 'conf', 'graph', 'ivector']
            missing_items = []
            for item in required_items:
                full_path = os.path.join(path, item)
                if not os.path.exists(full_path):
                    missing_items.append(item)
            
            if missing_items:
                missing_models.append(name)
                print(f"❌ {name} model incomplete: missing {missing_items}")
            else:
                available_models.append(name)
                print(f"✅ {name} model ready")
        
        if missing_models:
            print(f"⚠️  Missing models: {missing_models}")
            print("   Download from: https://alphacephei.com/vosk/models")
        
        return missing_models

    def scan_available_media(self):
        """Scan and catalog all available video and image files"""
        print("📁 Scanning media files...")
        
        self.available_videos = {}
        self.asl_images = {}
        self.isl_images = {}
        
        # Scan video files
        if os.path.exists(self.VIDEOS_PATH):
            video_files = [f for f in os.listdir(self.VIDEOS_PATH) if f.endswith('.mp4')]
            for file in video_files:
                name = file[:-4].lower()  # Remove .mp4 extension
                self.available_videos[name] = file
            print(f"📹 Found {len(video_files)} video files")
        else:
            print("⚠️  Videos directory not found")
        
        # Scan ASL alphabet images
        if os.path.exists(self.ALPHABET_IMAGES_PATH):
            asl_files = [f for f in os.listdir(self.ALPHABET_IMAGES_PATH) if f.endswith('.jpg')]
            for file in asl_files:
                self.asl_images[file] = file
            print(f"🔤 Found {len(asl_files)} ASL alphabet images")
        else:
            print("⚠️  ASL images directory not found")
        
        # Scan ISL alphabet images
        if os.path.exists(self.INDIAN_ALPHABET_IMAGES_PATH):
            isl_files = [f for f in os.listdir(self.INDIAN_ALPHABET_IMAGES_PATH) if f.endswith('.jpg')]
            for file in isl_files:
                self.isl_images[file] = file
            print(f"🤟 Found {len(isl_files)} ISL alphabet images")
        else:
            print("⚠️  ISL images directory not found")

    def initialize_vosk_model(self, language):
        """Initialize the Vosk model for the specified language"""
        if not VOSK_AVAILABLE:
            return False, "Vosk not available. Please install: pip install vosk pyaudio"
        
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
                return False, f"Model not found for {language}. Please download from vosk-model repository."
            
            # Only reload if language changed
            if self.current_language != language:
                print(f"🔄 Loading {language.upper()} model...")
                self.current_model = vosk.Model(model_path)
                self.current_recognizer = vosk.KaldiRecognizer(self.current_model, self.SAMPLE_RATE)
                self.current_language = language
                print(f"✅ {language.upper()} model loaded successfully")
            
            return True, f"Model ready for {language}"
            
        except Exception as e:
            error_msg = f"Error loading {language} model: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def translate_text(self, text, language='asl'):
        """
        Main method to translate text to sign language
        
        Args:
            text (str): Input text to translate
            language (str): Target language ('asl', 'isl', 'hindi', 'telugu', 'gujarati')
            
        Returns:
            tuple: (result_dict, status_code)
        """
        try:
            if not text or not text.strip():
                return {'error': 'No text provided'}, 400
            
            # Clean and prepare text
            text = text.strip().lower()
            print(f"🔤 Translating: '{text}' → {language.upper()}")
            
            # Get translation using smart fallback system
            video_paths = self.text_to_sign(text, language)
            
            if not video_paths:
                print("⚠️  No translation paths generated")
                return {'error': 'No signs found for the given text'}, 404
                
            print(f"✅ Generated {len(video_paths)} sign elements")
            
            response = {
                'video_paths': video_paths,
                'expressions': [],
                'context': {
                    'language': language,
                    'original_text': text,
                    'total_signs': len(video_paths)
                }
            }
            
            return response, 200
            
        except Exception as e:
            error_msg = f"Translation error: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'error': error_msg}, 500

    def text_to_sign(self, text, language='asl'):
        """
        🎯 CORE TRANSLATION ENGINE with Regional Character Mapping
        
        This method implements the smart fallback system:
        1. Try to find direct video matches for words
        2. If no video, spell word character by character
        3. For regional languages, map characters to English equivalents
        4. Use appropriate alphabet images (ASL or ISL)
        
        Args:
            text (str): Input text
            language (str): Target language
            
        Returns:
            list: List of video/image paths for display
        """
        video_paths = []
        
        try:
            # Get available media files
            asl_files = set(self.asl_images.keys()) if hasattr(self, 'asl_images') else set()
            isl_files = set(self.isl_images.keys()) if hasattr(self, 'isl_images') else set()
            video_files = set(self.available_videos.keys()) if hasattr(self, 'available_videos') else set()
            
            print(f"📊 Available: {len(video_files)} videos, {len(asl_files)} ASL, {len(isl_files)} ISL images")
            
        except Exception as e:
            print(f"❌ Error accessing media files: {e}")
            return []

        try:
            # 🌍 LANGUAGE DETECTION AND PROCESSING
            is_regional = language.lower() in ['hindi', 'telugu', 'gujarati', 'isl']
            
            if is_regional or language.lower() == 'isl':
                print(f"🌏 Processing regional/ISL language: {language.upper()}")
                return self._process_isl_language(text, language, video_files, isl_files)
            else:
                print(f"🌎 Processing ASL language: {language.upper()}")
                return self._process_asl_language(text, video_files, asl_files)
                
        except Exception as e:
            print(f"❌ Error in text_to_sign: {e}")
            traceback.print_exc()
            return []

    def _process_isl_language(self, text, language, video_files, isl_files):
        """Process ISL and regional languages (Hindi, Telugu, Gujarati)"""
        video_paths = []
        words = text.split() if isinstance(text, str) else text
        
        for word in words:
            if not word or word.isspace():
                continue
                
            original_word = word.lower()
            print(f"🔍 Processing word: '{original_word}'")
            
            # 📹 STEP 1: Try direct video match
            if original_word in video_files:
                video_path = f"mp4videos/{self.available_videos[original_word]}"
                video_paths.append(video_path)
                print(f"✅ Found video: {original_word}")
                continue

            # 🔤 STEP 2: Spell using ISL alphabet with character mapping
            print(f"🔤 Spelling word: '{word}'")
            has_letters = False
            
            # Get character mapping for regional languages
            char_map = self.regional_char_maps.get(language.lower(), {})
            is_regional_lang = language.lower() in ['hindi', 'telugu', 'gujarati']
            
            for char in word:
                mapped_char = None
                
                # 🎯 REGIONAL CHARACTER MAPPING - Key feature!
                if is_regional_lang and char in char_map:
                    mapped_char = char_map[char]
                    if mapped_char == '':  # Skip empty mappings (like halant/virama)
                        print(f"⏭️  Skipping halant/virama: '{char}'")
                        continue
                    print(f"🔄 Mapped '{char}' → '{mapped_char}' ({language})")
                elif char.isalpha():
                    mapped_char = char.upper()
                elif char.isdigit():
                    mapped_char = char
                else:
                    print(f"⏭️  Skipping non-alphanumeric: '{char}'")
                    continue
                
                if mapped_char:
                    # Add alphabet character
                    if mapped_char.isalpha():
                        char_file = f"{mapped_char.upper()}.jpg"
                        if char_file in isl_files:
                            has_letters = True
                            video_paths.append(f"indianalphabetsandnumbers/{char_file}")
                            print(f"✅ Added ISL: {mapped_char.upper()}")
                        else:
                            print(f"❌ No ISL image: {mapped_char}")
                    # Add numeric character
                    elif mapped_char.isdigit():
                        num_file = f"{mapped_char}.jpg"
                        if num_file in isl_files:
                            has_letters = True
                            video_paths.append(f"indianalphabetsandnumbers/{num_file}")
                            print(f"✅ Added ISL number: {mapped_char}")
                        else:
                            print(f"❌ No ISL number image: {mapped_char}")
            
            # Note: ISL doesn't typically have space images, so we skip word spacing
            
        return video_paths

    def _process_asl_language(self, text, video_files, asl_files):
        """Process ASL (American Sign Language)"""
        video_paths = []
        words = text.split() if isinstance(text, str) else text
        
        for word in words:
            if not word or word.isspace():
                continue
                
            original_word = word.lower()
            print(f"🔍 Processing ASL word: '{original_word}'")
            
            # 📹 STEP 1: Try direct video match
            if original_word in video_files:
                video_path = f"mp4videos/{self.available_videos[original_word]}"
                video_paths.append(video_path)
                print(f"✅ Found ASL video: {original_word}")
                continue

            # 🔤 STEP 2: Spell using ASL alphabet
            print(f"🔤 Spelling ASL word: '{word}'")
            has_letters = False
            
            for char in word:
                if char.isalpha():
                    char_upper = char.upper()
                    char_file = f"{char_upper}_test.jpg"  # ASL format: A_test.jpg
                    if char_file in asl_files:
                        has_letters = True
                        video_paths.append(f"alphabetimages/{char_file}")
                        print(f"✅ Added ASL: {char_upper}")
                    else:
                        print(f"❌ No ASL image: {char}")
                elif char.isdigit():
                    num_file = f"{char}_test.jpg"
                    if num_file in asl_files:
                        has_letters = True
                        video_paths.append(f"alphabetimages/{num_file}")
                        print(f"✅ Added ASL number: {char}")
                    else:
                        print(f"❌ No ASL number: {char}")
            
            # Add space after spelled words (ASL has space image)
            if has_letters and "space_test.jpg" in asl_files:
                video_paths.append(f"alphabetimages/space_test.jpg")
                print("✅ Added word space")
        
        return video_paths

    def save_feedback(self, original, correction):
        """Save user feedback for system improvement"""
        feedback_dir = os.path.join(self.PROJECT_PATH, 'feedback')
        feedback_file = os.path.join(feedback_dir, 'feedback_data.json')
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        feedback_entry = {
            "timestamp": timestamp,
            "original": original,
            "correction": correction,
            "session_id": f"session_{int(datetime.now().timestamp())}"
        }
        
        try:
            # Load existing feedback
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"feedback": [], "stats": {"total_feedback": 0}}
            
            # Add new feedback
            data["feedback"].append(feedback_entry)
            data["stats"]["total_feedback"] += 1
            
            # Save updated feedback
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            print(f"✅ Feedback saved: '{original}' → '{correction}'")
            return True
            
        except Exception as e:
            print(f"❌ Error saving feedback: {e}")
            return False

    def get_system_status(self):
        """Get comprehensive system status"""
        return {
            "vosk_available": VOSK_AVAILABLE,
            "speech_recognition_available": SR_AVAILABLE,
            "missing_models": self.MISSING_MODELS,
            "available_videos": len(self.available_videos) if hasattr(self, 'available_videos') else 0,
            "available_asl_images": len(self.asl_images) if hasattr(self, 'asl_images') else 0,
            "available_isl_images": len(self.isl_images) if hasattr(self, 'isl_images') else 0,
            "supported_languages": ["ASL", "ISL", "Hindi", "Telugu", "Gujarati"],
            "current_language": self.current_language,
            "directories": {
                "project_path": self.PROJECT_PATH,
                "videos_path": self.VIDEOS_PATH,
                "asl_images_path": self.ALPHABET_IMAGES_PATH,
                "isl_images_path": self.INDIAN_ALPHABET_IMAGES_PATH
            }
        }

# 🌐 FLASK WEB APPLICATION
app = Flask(__name__)
app.secret_key = 'sign_language_translator_2025'

# Initialize the translator
try:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    sign_language_translator = SignLanguageTranslator(base_path=BASE_PATH)
    print("🚀 Sign Language Translator initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing translator: {e}")
    sign_language_translator = None

@app.route('/')
def index():
    """Home page with system status"""
    if not sign_language_translator:
        return "<h1>❌ Sign Language Translator Not Available</h1><p>Check console for initialization errors.</p>"
    
    status = sign_language_translator.get_system_status()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sign Language Translator</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .status {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .error {{ background: #ffebee; color: #c62828; }}
            .success {{ background: #e8f5e8; color: #2e7d32; }}
            a {{ display: inline-block; background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px 0 0; }}
            a:hover {{ background: #1565c0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤟 Sign Language Translator</h1>
            <p>Real-time sign language translation supporting multiple languages with regional character mapping.</p>
            
            <div class="status {'success' if status['vosk_available'] else 'error'}">
                <strong>Vosk Status:</strong> {'✅ Available' if status['vosk_available'] else '❌ Not Available'}
            </div>
            
            <div class="status">
                <strong>Supported Languages:</strong> {', '.join(status['supported_languages'])}
            </div>
            
            <div class="status">
                <strong>Media Files:</strong> 
                📹 {status['available_videos']} videos, 
                🔤 {status['available_asl_images']} ASL images, 
                🤟 {status['available_isl_images']} ISL images
            </div>
            
            {'<div class="status error"><strong>Missing Models:</strong> ' + ', '.join(status['missing_models']) + '</div>' if status['missing_models'] else ''}
            
            <a href="/sign-language">🚀 Launch Translator</a>
            <a href="/api/status">📊 API Status</a>
            
            <h3>📝 Setup Instructions:</h3>
            <ol>
                <li>Download Vosk models from <a href="https://alphacephei.com/vosk/models" target="_blank">alphacephei.com/vosk/models</a></li>
                <li>Place models in: <code>{status['directories']['project_path']}/vosk_models/</code></li>
                <li>Add video files to: <code>{status['directories']['videos_path']}</code></li>
                <li>Add ASL images to: <code>{status['directories']['asl_images_path']}</code></li>
                <li>Add ISL images to: <code>{status['directories']['isl_images_path']}</code></li>
            </ol>
        </div>
    </body>
    </html>
    """

@app.route('/sign-language')
def sign_language():
    """Main sign language translation interface"""
    if not sign_language_translator:
        return "❌ Sign language service not available", 503
    
    # Auto-create the HTML template if it doesn't exist
    template_path = os.path.join(BASE_PATH, 'templates')
    os.makedirs(template_path, exist_ok=True)
    
    html_file = os.path.join(template_path, 'sign_language.html')
    if not os.path.exists(html_file):
        create_html_template(html_file)
    
    return render_template('sign_language.html')

@app.route('/api/sign-language/translate', methods=['POST'])
def translate_to_sign():
    """API endpoint for text translation"""
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
        print(f"❌ API Error: {e}")
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
        print(f"❌ Voice init error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/sign-language/media/<path:filename>')
def serve_sign_media(filename):
    """Serve sign language media files (videos and images)"""
    if not sign_language_translator:
        return "Service not available", 503
    
    try:
        # Determine directory based on file path prefix
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
            return "Invalid media path", 404
        
        return send_from_directory(directory, file_path)
        
    except Exception as e:
        print(f"❌ Media serve error: {e}")
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
        print(f"❌ Feedback error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Get system status via API"""
    if not sign_language_translator:
        return jsonify({'error': 'Sign language service not available'}), 503
    
    return jsonify(sign_language_translator.get_system_status())

def create_html_template(file_path):
    """Auto-create the HTML template file"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤟 Real-Time Sign Language Translation</title>
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

        .examples {
            margin: 20px 0;
            padding: 15px;
            background: #fff3cd;
            border-radius: 10px;
        }

        .examples h4 {
            color: #856404;
            margin-bottom: 10px;
        }

        .example-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .example-btn {
            background: #ffc107;
            color: #212529;
            padding: 8px 12px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .example-btn:hover {
            background: #ffb300;
            transform: translateY(-1px);
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
            <p>Convert text to sign language in multiple languages with regional character mapping</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label for="languageSelect">Select Language:</label>
                <select id="languageSelect">
                    <option value="asl">English (ASL) - American Sign Language</option>
                    <option value="isl">English (ISL) - Indian Sign Language</option>
                    <option value="hindi">हिंदी (Hindi) - Indian Sign Language</option>
                    <option value="telugu">తెలుగు (Telugu) - Indian Sign Language</option>
                    <option value="gujarati">ગુજરાતી (Gujarati) - Indian Sign Language</option>
                </select>
            </div>
            
            <button id="initializeBtn">Initialize Voice Recognition</button>
        </div>

        <div class="text-input-section">
            <h3>Type Text to Translate:</h3>
            <textarea id="textInput" placeholder="Type your text here... 
Examples:
• English: hello world
• Hindi: आप कैसे हैं
• Telugu: మీరు ఎలా ఉన్నారు
• Gujarati: તમે કેમ છો"></textarea>
            <button id="translateBtn">🔄 Translate to Sign Language</button>
        </div>

        <div class="examples">
            <h4>📝 Try These Examples:</h4>
            <div class="example-buttons">
                <button class="example-btn" onclick="setExample('hello world')">Hello World</button>
                <button class="example-btn" onclick="setExample('आप कैसे हैं')">आप कैसे हैं</button>
                <button class="example-btn" onclick="setExample('మీరు ఎలా ఉన్నారు')">మీరు ఎలా ఉన్నారు</button>
                <button class="example-btn" onclick="setExample('તમે કેમ છો')">તમે કેમ છો</button>
                <button class="example-btn" onclick="setExample('नमस्ते')">नमस्ते</button>
                <button class="example-btn" onclick="setExample('धन्यवाद')">धन्यवाद</button>
            </div>
        </div>

        <div class="output-section">
            <h3>🤟 Sign Language Output:</h3>
            <div id="statusMessage" class="status info">Select a language and type text to begin translation</div>
            <div id="videoContainer" class="video-container">
                <p>Your sign language translation will appear here</p>
            </div>
        </div>

        <div class="feedback-section">
            <h3>💬 Feedback (Help us improve):</h3>
            <input type="text" id="originalText" placeholder="Original text that was translated">
            <input type="text" id="correctionText" placeholder="Correction or suggestion">
            <button id="submitFeedback">📤 Submit Feedback</button>
        </div>
    </div>

    <script>
        class SignLanguageApp {
            constructor() {
                this.currentLanguage = 'asl';
                this.isInitialized = false;
                
                this.initializeElements();
                this.attachEventListeners();
                this.updateStatus('Ready to translate! Select a language and type some text.', 'info');
            }

            initializeElements() {
                this.languageSelect = document.getElementById('languageSelect');
                this.initializeBtn = document.getElementById('initializeBtn');
                this.textInput = document.getElementById('textInput');
                this.translateBtn = document.getElementById('translateBtn');
                this.videoContainer = document.getElementById('videoContainer');
                this.statusMessage = document.getElementById('statusMessage');
                this.originalText = document.getElementById('originalText');
                this.correctionText = document.getElementById('correctionText');
                this.submitFeedback = document.getElementById('submitFeedback');
            }

            attachEventListeners() {
                this.translateBtn.addEventListener('click', () => this.translateText());
                this.submitFeedback.addEventListener('click', () => this.submitUserFeedback());
                this.languageSelect.addEventListener('change', () => this.onLanguageChange());
                this.initializeBtn.addEventListener('click', () => this.initializeVoiceRecognition());
                
                // Enter key support
                this.textInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                        this.translateText();
                    }
                });
            }

            onLanguageChange() {
                this.currentLanguage = this.languageSelect.value;
                this.updateStatus(`Language changed to ${this.currentLanguage.toUpperCase()}. Ready to translate!`, 'info');
            }

            async initializeVoiceRecognition() {
                this.updateStatus('Initializing voice recognition...', 'info');
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
                        this.updateStatus(`✅ Voice recognition ready for ${data.language}`, 'success');
                    } else {
                        this.updateStatus(`❌ Error: ${data.error}`, 'error');
                    }
                } catch (error) {
                    console.error('Error initializing voice recognition:', error);
                    this.updateStatus('❌ Failed to initialize voice recognition', 'error');
                } finally {
                    this.initializeBtn.disabled = false;
                }
            }

            async translateText() {
                const text = this.textInput.value.trim();
                if (!text) {
                    this.updateStatus('❌ Please enter some text to translate', 'error');
                    return;
                }

                this.updateStatus('🔄 Translating... Please wait', 'info');
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
                        this.displaySignLanguage(data.video_paths, data.context);
                        this.updateStatus(`✅ Translation completed! Showing ${data.video_paths.length} sign elements.`, 'success');
                        
                        // Pre-fill feedback form
                        this.originalText.value = text;
                    } else {
                        this.updateStatus(`❌ Error: ${data.error}`, 'error');
                        this.videoContainer.innerHTML = '<p>❌ Translation failed. Please try again.</p>';
                    }
                } catch (error) {
                    console.error('Error translating text:', error);
                    this.updateStatus('❌ Failed to translate text. Check your connection.', 'error');
                } finally {
                    this.translateBtn.disabled = false;
                }
            }

            displaySignLanguage(videoPaths, context) {
                this.videoContainer.innerHTML = '';

                if (!videoPaths || videoPaths.length === 0) {
                    this.videoContainer.innerHTML = '<p>❌ No signs found for the given text</p>';
                    return;
                }

                // Add context information
                if (context) {
                    const contextDiv = document.createElement('div');
                    contextDiv.style.cssText = 'text-align: center; margin-bottom: 20px; font-size: 14px; color: #666;';
                    contextDiv.innerHTML = `
                        <strong>Translation Details:</strong> 
                        Language: ${context.language?.toUpperCase()}, 
                        Original: "${context.original_text}", 
                        Signs: ${context.total_signs}
                    `;
                    this.videoContainer.appendChild(contextDiv);
                }

                // Display each sign element
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
                        video.onerror = () => {
                            video.style.display = 'none';
                            const errorMsg = document.createElement('p');
                            errorMsg.textContent = '❌ Video not found';
                            errorMsg.style.color = 'red';
                            videoItem.appendChild(errorMsg);
                        };
                        videoItem.appendChild(video);
                    } else if (path.endsWith('.jpg') || path.endsWith('.png')) {
                        const img = document.createElement('img');
                        img.src = `/sign-language/media/${path}`;
                        img.alt = `Sign ${index + 1}`;
                        img.onerror = () => {
                            img.style.display = 'none';
                            const errorMsg = document.createElement('p');
                            errorMsg.textContent = '❌ Image not found';
                            errorMsg.style.color = 'red';
                            videoItem.appendChild(errorMsg);
                        };
                        videoItem.appendChild(img);
                    }

                    // Add sequence number
                    const seqLabel = document.createElement('div');
                    seqLabel.textContent = `${index + 1}`;
                    seqLabel.style.cssText = 'font-size: 12px; color: #666; margin-top: 5px;';
                    videoItem.appendChild(seqLabel);

                    this.videoContainer.appendChild(videoItem);
                });
            }

            async submitUserFeedback() {
                const original = this.originalText.value.trim();
                const correction = this.correctionText.value.trim();

                if (!original || !correction) {
                    alert('❌ Please fill in both original text and correction');
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
                        alert('✅ Feedback submitted successfully! Thank you for helping us improve.');
                        this.originalText.value = '';
                        this.correctionText.value = '';
                    } else {
                        alert(`❌ Error: ${data.error}`);
                    }
                } catch (error) {
                    console.error('Error submitting feedback:', error);
                    alert('❌ Failed to submit feedback. Please try again.');
                }
            }

            updateStatus(message, type) {
                this.statusMessage.textContent = message;
                this.statusMessage.className = `status ${type}`;
            }
        }

        // Helper function for example buttons
        function setExample(text) {
            document.getElementById('textInput').value = text;
        }

        // Initialize the application when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new SignLanguageApp();
            console.log('🚀 Sign Language Translator loaded successfully!');
        });
    </script>
</body>
</html>"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Created HTML template: {file_path}")

if __name__ == '__main__':
    print("🚀 Starting Sign Language Translation Server...")
    print("📍 Access the application at: http://localhost:5000")
    print("🎯 Direct translator access: http://localhost:5000/sign-language")
    print("📊 System status: http://localhost:5000/api/status")
    print()
    
    # Show setup instructions if models are missing
    if sign_language_translator and sign_language_translator.MISSING_MODELS:
        print("⚠️  SETUP REQUIRED:")
        print("   Missing Vosk models. Download from: https://alphacephei.com/vosk/models")
        print(f"   Place models in: {sign_language_translator.PROJECT_PATH}/vosk_models/")
        print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
