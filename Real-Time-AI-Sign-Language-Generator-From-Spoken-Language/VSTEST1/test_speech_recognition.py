import os
import pyaudio
import json
from vosk import Model, KaldiRecognizer
import traceback

# Paths
PROJECT_PATH = r"/Users/pardhu/vsc/sarathi/sign language/Real-Time-AI-Sign-Language-Generator-From-Spoken-Language/VSTEST1"

# Model paths
MODEL_PATHS = {
    'ASL': os.path.join(PROJECT_PATH, "vosk-model-small-en-us-0.15"),
    'ISL': os.path.join(PROJECT_PATH, "vosk-model-en-in-0.5"),
    'Hindi': os.path.join(PROJECT_PATH, "vosk-model-small-hi-0.22"),
    'Telugu': os.path.join(PROJECT_PATH, "vosk-model-small-te-0.42"),
    'Gujarati': os.path.join(PROJECT_PATH, "vosk-model-small-gu-0.42")
}

def initialize_model(language='asl'):
    """Initialize the appropriate speech recognition model based on language"""
    try:
        if language.lower() == 'telugu':
            if not os.path.exists(MODEL_PATHS['Telugu']):
                print("Telugu model not found!")
                return None
            model = Model(MODEL_PATHS['Telugu'])
            print("Telugu model loaded successfully")
            
        # ... other language cases ...
        
        return model
    except Exception as e:
        print(f"Error initializing model: {e}")
        traceback.print_exc()
        return None

def process_audio_stream(model, language='asl'):
    """Process audio stream and return recognized text"""
    try:
        # For Telugu, we need to ensure proper encoding
        if language.lower() == 'telugu':
            rec = KaldiRecognizer(model, 16000, '{"language": "te"}')
            print("Telugu recognition initialized")
        else:
            rec = KaldiRecognizer(model, 16000)

        # ... rest of the function ...

def handle_recognition_result(result, language='asl'):
    """Handle the recognition result based on language"""
    try:
        if language.lower() == 'telugu':
            # Telugu specific handling
            if 'result' in result:
                return result['text']  # Use text field for Telugu
            elif 'partial' in result:
                return result['partial']
        
        # ... handling for other languages ...
        
    except Exception as e:
        print(f"Error handling recognition result: {e}")
        return ""

def test_model(language):
    """Test speech recognition for a specific language"""
    model_path = MODEL_PATHS[language]
    
    if not os.path.exists(model_path):
        print(f"❌ {language} model not found at: {model_path}")
        return
        
    print(f"\nTesting {language} speech recognition...")
    print("=" * 50)
    print(f"Model path: {model_path}")
    
    try:
        # Initialize model
        model = Model(str(model_path))
        recognizer = KaldiRecognizer(model, 16000)
        
        # Set up audio
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )
        
        print(f"\n🎤 Listening for {language} speech...")
        print("Speak something (Ctrl+C to stop)")
        
        # Start recognition
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get('text', '').strip()
                if text:
                    print(f"Recognized ({language}): {text}")
            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get('partial', '').strip()
                if partial_text:
                    print(f"Partial ({language}): {partial_text}", end='\r')
                    
    except KeyboardInterrupt:
        print("\n\nStopping recognition...")
    except Exception as e:
        print(f"\n❌ Error testing {language} model: {str(e)}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        if 'audio' in locals():
            audio.terminate()
        print(f"\n{language} test completed")

def main():
    print("Speech Recognition Model Tester")
    print("=" * 50)
    
    while True:
        print("\nAvailable languages:")
        for i, lang in enumerate(MODEL_PATHS.keys(), 1):
            print(f"{i}. {lang}")
        print("0. Exit")
        
        try:
            choice = input("\nSelect a language to test (0-5): ").strip()
            if choice == '0':
                break
                
            if choice.isdigit() and 1 <= int(choice) <= len(MODEL_PATHS):
                language = list(MODEL_PATHS.keys())[int(choice)-1]
                test_model(language)
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 