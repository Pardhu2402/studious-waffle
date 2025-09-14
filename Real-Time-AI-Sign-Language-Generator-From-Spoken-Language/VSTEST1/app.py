from flask import Flask, render_template, request, jsonify, send_file, Response, send_from_directory
from flask_cors import CORS
import os
import tempfile
import base64
import pyaudio
import json
import threading
import queue
import time
from vosk import Model, KaldiRecognizer
from datetime import datetime

# Import after verifying model loads correctly
from voice_to_sign import *
from sign_translator import SignTranslator
from voice_to_sign import load_model, MISSING_MODELS

app = Flask(__name__)

# Update CORS settings
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS", "HEAD"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Accept-Language", 
                         "Origin", "X-Requested-With"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, HEAD'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Accept-Language, Origin, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# Initialize translator
translator = SignTranslator()

# Update the audio settings
CHUNK_SIZE = 1024  # Smaller chunk for faster processing
SAMPLE_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
audio_queue = queue.Queue(maxsize=10)  # Limit queue size to prevent lag
is_recording = False
current_model = None  # Will store the currently selected model
current_recognizer = None
current_language = None  # Added to store the current language

# Update these paths at the top of the file
VIDEOS_PATH = r"/Users/sreemadhav/SreeMadhav/prototype1 drive/Prototype1signl/VSTEST1/mp4videos"
ALPHABET_IMAGES_PATH = r"/Users/sreemadhav/SreeMadhav/prototype1 drive/Prototype1signl/VSTEST1/alphabetimages"
INDIAN_ALPHABET_IMAGES_PATH = r"/Users/sreemadhav/SreeMadhav/prototype1 drive/Prototype1signl/VSTEST1/indianalphabetsandnumbers"

FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), 'feedback')
FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, 'feedback_data.json')
FEEDBACK_LOG = os.path.join(FEEDBACK_DIR, 'feedback.log')

@app.route('/select_language', methods=['POST'])
def select_language():
    global current_model, current_recognizer, is_recording, current_language
    
    # Stop any existing stream
    is_recording = False
    time.sleep(0.1)  # Give time for cleanup
    
    try:
        language = request.json.get('language', '').lower()
        if not language:
            return jsonify({'error': 'No language specified'}), 400
            
        # Store current language
        current_language = language
            
        # Check if model is available
        if language.upper() in MISSING_MODELS:
            return jsonify({
                'error': f'Model for {language.upper()} is not available. Please check model installation.'
            }), 400
            
        try:
            # Load the model using the new function
            current_model, current_recognizer = load_model(language)
            print(f"{language.upper()} model loaded and ready")
            return jsonify({'status': f'{language.upper()} selected'})
            
        except FileNotFoundError as e:
            print(f"Model not found: {str(e)}")
            return jsonify({'error': f'Model not found for {language.upper()}'}), 404
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return jsonify({'error': f'Failed to load {language.upper()} model: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Error in language selection: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_audio_stream():
    global is_recording, current_recognizer, current_language
    
    if not current_recognizer:
        yield f"data: {json.dumps({'error': 'Please select a language first'})}\n\n"
        return

    print("Starting audio stream processing...")
    audio = None
    stream = None
    last_text = ""
    buffer_time = 0.3  # 300ms buffer for word completion
    last_word_time = time.time()
    
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=None
        )
        
        print("Audio stream opened successfully")
        
        while is_recording:
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                current_time = time.time()
                
                # Process partial results for immediate word recognition
                partial = current_recognizer.PartialResult()
                partial_dict = json.loads(partial)
                partial_text = partial_dict.get('partial', '').strip()
                
                if partial_text:
                    current_words = partial_text.split()
                    last_words = last_text.split()
                    
                    # Process new complete words
                    if len(current_words) > len(last_words):
                        # Get the new word
                        new_word = current_words[-1]
                        
                        # Only process if enough time has passed since last word
                        if current_time - last_word_time >= buffer_time:
                            if new_word.strip():
                                print(f"New word recognized: {new_word}")
                                response_data = {
                                    'text': new_word,
                                    'language': current_language,
                                    'is_word': True
                                }
                                yield f"data: {json.dumps(response_data)}\n\n"
                                last_word_time = current_time
                    
                    # Update display with current partial
                    yield f"data: {json.dumps({'partial': partial_text})}\n\n"
                    last_text = partial_text
                
                # Process final results
                if current_recognizer.AcceptWaveform(data):
                    result = current_recognizer.Result()
                    result_dict = json.loads(result)
                    text = result_dict.get('text', '').strip()
                    
                    if text:
                        # Process any remaining new words
                        current_words = text.split()
                        last_words = last_text.split()
                        new_words = [w for w in current_words if w not in last_words]
                        
                        for word in new_words:
                            if word.strip():
                                print(f"New word recognized (final): {word}")
                                response_data = {
                                    'text': word,
                                    'language': current_language,
                                    'is_word': True
                                }
                                yield f"data: {json.dumps(response_data)}\n\n"
                                last_word_time = current_time
                        
                        # Update display with final text
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_stream', methods=['GET'])
def start_stream():
    global is_recording
    
    # Make sure any previous stream is stopped
    is_recording = False
    time.sleep(0.1)  # Give time for cleanup
    
    # Start new stream
    is_recording = True
    
    return Response(
        process_audio_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global is_recording
    is_recording = False
    time.sleep(0.1)  # Give time for cleanup
    return jsonify({'status': 'stopped'})

@app.route('/translate_text', methods=['POST'])
def translate_text():
    try:
        text = request.json.get('text', '')
        language = request.json.get('language', 'asl')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        print(f"Translating text: '{text}' to {language}")
        
        # Get translation with context
        translation = translator.translate(text, language)
        
        # Convert to video paths
        video_paths = text_to_sign(translation['signs'], language)
        
        if not video_paths:
            print("Warning: No video paths generated for text")
            return jsonify({'error': 'No signs found for the given text'}), 404
            
        print(f"Generated {len(video_paths)} video paths")
        
        response = {
            'video_paths': video_paths,
            'expressions': translation['expressions'],
            'context': translation.get('context', {})
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in translate_text: {str(e)}")
        return jsonify({'error': str(e)}), 500

def save_feedback(original, correction):
    """Save feedback to both JSON and log file"""
    # Create feedback directory if it doesn't exist
    if not os.path.exists(FEEDBACK_DIR):
        os.makedirs(FEEDBACK_DIR)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save to JSON file
    feedback_entry = {
        "timestamp": timestamp,
        "original": original,
        "correction": correction
    }
    
    try:
        # Load existing feedback
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"feedback": []}
        
        # Add new feedback
        data["feedback"].append(feedback_entry)
        
        # Save updated feedback
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        # Also log to text file
        with open(FEEDBACK_LOG, 'a', encoding='utf-8') as f:
            f.write(f'[{timestamp}] Original: "{original}" -> Correction: "{correction}"\n')
            
        return True
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return False

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """Handle feedback submission"""
    try:
        data = request.get_json()
        original = data.get('original')
        correction = data.get('correction')
        
        if not original or not correction:
            return jsonify({"status": False, "error": "Missing required fields"})
            
        if save_feedback(original, correction):
            return jsonify({"status": True})
        else:
            return jsonify({"status": False, "error": "Failed to save feedback"})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

@app.route('/media/<path:filename>')
def serve_media(filename):
    # First try alphabetimages
    if filename.startswith('alphabetimages/'):
        return send_from_directory(ALPHABET_IMAGES_PATH, filename.replace('alphabetimages/', ''))
    # Then try indianalphabetsandnumbers
    elif filename.startswith('indianalphabetsandnumbers/'):
        return send_from_directory(INDIAN_ALPHABET_IMAGES_PATH, filename.replace('indianalphabetsandnumbers/', ''))
    # Finally try mp4videos
    elif filename.startswith('mp4videos/'):
        return send_from_directory(VIDEOS_PATH, filename.replace('mp4videos/', ''))
    else:
        return "File not found", 404

def check_model_setup():
    """Check if models are properly set up before starting the server"""
    if MISSING_MODELS:
        print("\nWARNING: Some speech recognition models are missing or incomplete!")
        print("The following languages will not be available:")
        for model in MISSING_MODELS:
            print(f"- {model}")
        print("\nPlease download missing models from:")
        print("https://alphacephei.com/vosk/models")
        print("And place them in the appropriate directories under VSTEST1/models/")
        return False
    return True

if __name__ == '__main__':
    if not check_model_setup():
        print("\nContinuing with limited functionality...")
    
    # Get local IP address
    import socket
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    host = get_ip()
    port = 5001
    print(f"\nAccess your app at:")
    print(f"Local URL: http://{host}:{port}")
    
    app.run(
        host='0.0.0.0',  # Makes the server accessible from other devices
        port=port,
        debug=True
    ) 