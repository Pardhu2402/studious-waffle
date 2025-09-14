"""
Sign Language Translation Utility Module
Integrates the sign language functionality into Sahayak
"""
import os
import sys
import json
import time
import threading
import queue
from pathlib import Path
import traceback
import stat

# Try importing required packages with fallback
try:
    from vosk import Model, KaldiRecognizer
    import pyaudio
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: Vosk or PyAudio not available. Sign language features will be limited.")

from flask import jsonify, Response
from datetime import datetime

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
        # Get the correct path to the VSTEST1 directory
        # From /Users/pardhu/vsc/sarathi/sign language/Sahayak-/sahayak_plus
        # Go up to sign language directory and then to Real-Time-AI... 
        base_dir = os.path.dirname(os.path.dirname(self.base_path))  # Go up 2 levels
        vstest_path = os.path.join(base_dir, 
                                   "Real-Time-AI-Sign-Language-Generator-From-Spoken-Language", 
                                   "VSTEST1")
        
        print(f"Debug: Base path: {self.base_path}")
        print(f"Debug: VSTEST1 path: {vstest_path}")
        print(f"Debug: VSTEST1 exists: {os.path.exists(vstest_path)}")
        
        self.PROJECT_PATH = vstest_path
        self.VIDEOS_PATH = os.path.join(vstest_path, "mp4videos")
        self.ALPHABET_IMAGES_PATH = os.path.join(vstest_path, "alphabetimages")
        self.INDIAN_ALPHABET_IMAGES_PATH = os.path.join(vstest_path, "indianalphabetsandnumbers")
        
        print(f"Debug: Videos path: {self.VIDEOS_PATH}")
        print(f"Debug: Videos exists: {os.path.exists(self.VIDEOS_PATH)}")
        
        # Model paths
        self.VOSK_MODEL_PATH_ISL = os.path.join(vstest_path, "vosk-model-en-in-0.5")
        self.VOSK_MODEL_PATH_ASL = os.path.join(vstest_path, "vosk-model-small-en-us-0.15")
        self.VOSK_MODEL_PATH_HINDI = os.path.join(vstest_path, "vosk-model-small-hi-0.22")
        self.VOSK_MODEL_PATH_TELUGU = os.path.join(vstest_path, "vosk-model-small-te-0.42")
        self.VOSK_MODEL_PATH_GUJARATI = os.path.join(vstest_path, "vosk-model-small-gu-0.42")
        
        # Create upload directory if needed
        self.UPLOAD_FOLDER = os.path.join(vstest_path, "uploads")
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
        
        # Check if directories exist
        if not os.path.exists(self.VIDEOS_PATH):
            print(f"Videos directory not found: {self.VIDEOS_PATH}")
            return
            
        if not os.path.exists(self.ALPHABET_IMAGES_PATH):
            print(f"ASL images directory not found: {self.ALPHABET_IMAGES_PATH}")
            return
            
        if not os.path.exists(self.INDIAN_ALPHABET_IMAGES_PATH):
            print(f"ISL images directory not found: {self.INDIAN_ALPHABET_IMAGES_PATH}")
            return

        # Scan MP4 videos
        try:
            for file in os.listdir(self.VIDEOS_PATH):
                if file.endswith('.mp4'):
                    base_name = file[:-4].lower()
                    self.available_videos[base_name] = file
        except Exception as e:
            print(f"Error scanning videos: {e}")
        
        # Scan ASL alphabet images
        try:
            for file in os.listdir(self.ALPHABET_IMAGES_PATH):
                if file.endswith('_test.jpg'):
                    base_name = file[:-9].lower()
                    self.asl_images[base_name] = file
            
            # Add special mappings
            self.asl_images['space'] = 'space_test.jpg'
            self.asl_images['nothing'] = 'nothing_test.jpg'
        except Exception as e:
            print(f"Error scanning ASL images: {e}")
        
        # Scan ISL alphabet images
        try:
            for file in os.listdir(self.INDIAN_ALPHABET_IMAGES_PATH):
                if file.endswith('.jpg'):
                    base_name = file[:-4].lower()
                    self.isl_images[base_name] = file
        except Exception as e:
            print(f"Error scanning ISL images: {e}")

    def load_model(self, language):
        """Load speech recognition model for specified language"""
        if not VOSK_AVAILABLE:
            raise Exception("Vosk not available. Please install vosk-api and pyaudio packages.")
            
        try:
            model_paths = {
                'isl': self.VOSK_MODEL_PATH_ISL,
                'asl': self.VOSK_MODEL_PATH_ASL,
                'hindi': self.VOSK_MODEL_PATH_HINDI,
                'telugu': self.VOSK_MODEL_PATH_TELUGU,
                'gujarati': self.VOSK_MODEL_PATH_GUJARATI
            }
            
            if language not in model_paths:
                raise ValueError(f"Unsupported language: {language}")
                
            model_path = model_paths[language]
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found for {language} at {model_path}")
                
            # Verify key directories exist
            required_dirs = ['am', 'conf', 'graph', 'ivector']
            for dir_name in required_dirs:
                if not os.path.exists(os.path.join(model_path, dir_name)):
                    raise FileNotFoundError(f"Required directory '{dir_name}' not found in {language} model")
            
            # Load the model
            model = Model(str(model_path))
            recognizer = KaldiRecognizer(model, 16000)
            print(f"{language.upper()} model loaded successfully")
            return model, recognizer
            
        except Exception as e:
            print(f"Error loading {language.upper()} model: {str(e)}")
            raise

    def select_language(self, language):
        """Select and load a language model"""
        try:
            # Stop any existing stream
            self.is_recording = False
            time.sleep(0.1)
            
            if not language:
                return {'error': 'No language specified'}, 400
                
            # Store current language
            self.current_language = language
                
            # Check if model is available
            if language.upper() in self.MISSING_MODELS:
                return {
                    'error': f'Model for {language.upper()} is not available. Please check model installation.'
                }, 400
                
            try:
                # Load the model
                self.current_model, self.current_recognizer = self.load_model(language)
                print(f"{language.upper()} model loaded and ready")
                return {'status': f'{language.upper()} selected'}, 200
                
            except FileNotFoundError as e:
                print(f"Model not found: {str(e)}")
                return {'error': f'Model not found for {language.upper()}'}, 404
                
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                return {'error': f'Failed to load {language.upper()} model: {str(e)}'}, 500
                
        except Exception as e:
            print(f"Error in language selection: {str(e)}")
            return {'error': str(e)}, 500

    def process_audio_stream(self):
        """Process audio stream for speech recognition"""
        if not VOSK_AVAILABLE:
            yield f"data: {json.dumps({'error': 'Speech recognition not available. Please install required packages.'})}\n\n"
            return
            
        if not self.current_recognizer:
            yield f"data: {json.dumps({'error': 'Please select a language first'})}\n\n"
            return

        print("Starting audio stream processing...")
        audio = None
        stream = None
        last_text = ""
        buffer_time = 0.3
        last_word_time = time.time()
        
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE,
                input_device_index=None
            )
            
            print("Audio stream opened successfully")
            
            while self.is_recording:
                try:
                    data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    current_time = time.time()
                    
                    # Process partial results
                    partial = self.current_recognizer.PartialResult()
                    partial_dict = json.loads(partial)
                    partial_text = partial_dict.get('partial', '').strip()
                    
                    if partial_text:
                        current_words = partial_text.split()
                        last_words = last_text.split()
                        
                        # Process new complete words
                        if len(current_words) > len(last_words):
                            new_word = current_words[-1]
                            
                            if current_time - last_word_time >= buffer_time:
                                if new_word.strip():
                                    print(f"New word recognized: {new_word}")
                                    response_data = {
                                        'text': new_word,
                                        'language': self.current_language,
                                        'is_word': True
                                    }
                                    yield f"data: {json.dumps(response_data)}\n\n"
                                    last_word_time = current_time
                        
                        # Update display with current partial
                        yield f"data: {json.dumps({'partial': partial_text})}\n\n"
                        last_text = partial_text
                    
                    # Process final results
                    if self.current_recognizer.AcceptWaveform(data):
                        result = self.current_recognizer.Result()
                        result_dict = json.loads(result)
                        text = result_dict.get('text', '').strip()
                        
                        if text:
                            current_words = text.split()
                            last_words = last_text.split()
                            new_words = [w for w in current_words if w not in last_words]
                            
                            for word in new_words:
                                if word.strip():
                                    print(f"New word recognized (final): {word}")
                                    response_data = {
                                        'text': word,
                                        'language': self.current_language,
                                        'is_word': True
                                    }
                                    yield f"data: {json.dumps(response_data)}\n\n"
                                    last_word_time = current_time
                            
                            yield f"data: {json.dumps({'text': text, 'is_full': True})}\n\n"
                            last_text = text
                            
                except Exception as e:
                    print(f"Error processing audio chunk: {e}")
                    continue

        except Exception as e:
            print(f"Error in audio stream setup: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            print("Cleaning up audio resources...")
            if stream:
                stream.stop_stream()
                stream.close()
            if audio:
                audio.terminate()
            print("Audio stream processing ended")

    def translate_text(self, text, language='asl'):
        """Convert text to sign language video paths"""
        try:
            if not text:
                return {'error': 'No text provided'}, 400
                
            print(f"Translating text: '{text}' to {language}")
            
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
        """Convert text to sign language video paths"""
        video_paths = []
        
        try:
            print(f"\\nChecking directories:")
            print(f"ASL Path: {self.ALPHABET_IMAGES_PATH}")
            print(f"ISL Path: {self.INDIAN_ALPHABET_IMAGES_PATH}")
            print(f"Videos Path: {self.VIDEOS_PATH}")
            
            # Verify directories exist
            if not os.path.exists(self.ALPHABET_IMAGES_PATH):
                print(f"Warning: ASL directory does not exist!")
                return []
            if not os.path.exists(self.INDIAN_ALPHABET_IMAGES_PATH):
                print(f"Warning: ISL directory does not exist!")
                return []
            if not os.path.exists(self.VIDEOS_PATH):
                print(f"Warning: Videos directory does not exist!")
                return []
            
            # Get available files
            asl_files = set(os.listdir(self.ALPHABET_IMAGES_PATH))
            isl_files = set(os.listdir(self.INDIAN_ALPHABET_IMAGES_PATH))
            video_files = set(os.listdir(self.VIDEOS_PATH))
            
            print(f"\\nFound files:")
            print(f"ASL files: {len(asl_files)}")
            print(f"ISL files: {len(isl_files)}")
            print(f"Video files: {len(video_files)}")
            
        except Exception as e:
            print(f"Error scanning directories: {e}")
            traceback.print_exc()
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
                    direct_video = f"{original_word}.mp4"
                    if direct_video in video_files:
                        video_paths.append(f"mp4videos/{direct_video}")
                        print(f"Found direct video match for: {original_word}")
                        video_found = True
                        continue

                    # If no video found, spell using ISL alphabet images
                    if not video_found:
                        print(f"No video found, spelling word: {word}")
                        has_letters = False
                        
                        # Get character mapping for regional languages
                        char_map = self.regional_char_maps.get(language.lower(), {})
                        is_regional = language.lower() in ['hindi', 'telugu', 'gujarati']
                        
                        for char in word:
                            mapped_char = None
                            
                            # For regional languages, try to map the character first
                            if is_regional and char in char_map:
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
                    direct_video = f"{original_word}.mp4"
                    if direct_video in video_files:
                        video_paths.append(f"mp4videos/{direct_video}")
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
                        if has_letters and "SPACE_test.jpg" in asl_files:
                            video_paths.append(f"alphabetimages/SPACE_test.jpg")

            if video_paths:
                print(f"Generated {len(video_paths)} video paths")
                print("Paths:", video_paths)
                return video_paths
            else:
                print("No signs found for the given text")
                # Return a "not found" sign if available
                error_sign = "not_understand.mp4"
                if error_sign in video_files:
                    return [f"mp4videos/{error_sign}"]
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
