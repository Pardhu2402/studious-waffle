# Real-Time Sign Language Translation System
## Technical Documentation and Implementation Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Directory Structure](#directory-structure)
4. [Components](#components)
5. [Implementation Details](#implementation-details)
6. [AI Models](#ai-models)
7. [Testing](#testing)
8. [Setup & Deployment](#setup--deployment)

## Project Overview

### Problem Statement
> "Real-Time Sign Language Generation from Spoken Language - Develop a real-time system that converts spoken language into visually accessible sign language (e.g., ASL, ISL). This system must accurately process audio input, accounting for natural language nuances and differing grammatical structures between spoken and sign languages, and generate dynamic, understandable visual representation of the appropriate sign language. The key is to accurately and dynamically bridge the communication gap in real-time, supporting multiple sign languages."

### Solution Architecture
A multi-layered system that:
- Processes real-time speech input using Vosk AI models
- Converts speech to text with language-specific processing
- Translates text to sign language using character mapping
- Renders visual output through videos and images
- Supports multiple languages (ASL, ISL, Hindi, Telugu, Gujarati)

## Directory Structure 

## Components

### 1. Speech Recognition System
```python
def process_audio_stream(model, language='asl'):
    """Process audio stream and return recognized text"""
    try:
        if language.lower() == 'telugu':
            rec = KaldiRecognizer(model, 16000, '{"language": "te"}')
            print("Telugu recognition initialized")
        else:
            rec = KaldiRecognizer(model, 16000)
        
        while is_recording:
            data = stream.read(CHUNK_SIZE)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                return result.get('text', '')
    except Exception as e:
        print(f"Error in audio processing: {e}")
        return ""
```

### 2. Translation System
```python
def text_to_sign(signs, language='asl'):
    """Convert text to sign language video paths"""
    video_paths = []
    try:
        # Process text and generate paths
        for word in signs.split():
            if word in video_dict:
                video_paths.append(f"mp4videos/{video_dict[word]}")
            else:
                # Spell word using alphabet images
                for char in word:
                    video_paths.append(get_alphabet_path(char, language))
        return video_paths
    except Exception as e:
        print(f"Translation error: {e}")
        return []
```

### 3. Character Mapping System
```python
regional_char_maps = {
    'hindi': {
        'अ': 'A', 'आ': 'A', 'इ': 'I', 'ई': 'I',
        'क': 'K', 'ख': 'K', 'ग': 'G', 'घ': 'G',
        # ... more mappings
    },
    'telugu': {
        'అ': 'A', 'ఆ': 'A', 'ఇ': 'I', 'ఈ': 'I',
        'క': 'K', 'ఖ': 'K', 'గ': 'G', 'ఘ': 'G',
        # ... more mappings
    },
    'gujarati': {
        'અ': 'A', 'આ': 'A', 'ઇ': 'I', 'ઈ': 'I',
        'ક': 'K', 'ખ': 'K', 'ગ': 'G', 'ઘ': 'G',
        # ... more mappings
    }
}
```

## AI Models

### Speech Recognition Models
1. **ASL Model (vosk-model-small-en-us-0.15)**
   - Size: 15MB
   - Purpose: English speech recognition
   - Accuracy: 90-95%

2. **ISL Model (vosk-model-en-in-0.5)**
   - Size: 50MB
   - Purpose: Indian English recognition
   - Accuracy: 85-90%

3. **Regional Models**
   - Hindi (vosk-model-small-hi-0.22)
   - Telugu (vosk-model-small-te-0.42)
   - Gujarati (vosk-model-small-gu-0.42)
   - Size: 20-40MB each
   - Accuracy: 80-85%

## Implementation Details

### Frontend Features
```html
<!-- Dark Theme UI -->
<html lang="en" data-bs-theme="dark">
    <!-- Language Selection -->
    <div class="language-selector mb-4">
        <div class="row">
            <div class="col-md-6">
                <h5>International</h5>
                <!-- ISL and ASL options -->
            </div>
            <div class="col-md-6">
                <h5>Regional</h5>
                <!-- Hindi, Telugu, Gujarati options -->
            </div>
        </div>
    </div>

    <!-- Playback Controls -->
    <div class="btn-group" role="group">
        <button class="btn speed-btn" data-speed="0.5">0.5x</button>
        <button class="btn speed-btn active" data-speed="1.0">1x</button>
        <button class="btn speed-btn" data-speed="1.5">1.5x</button>
        <button class="btn speed-btn" data-speed="2.0">2x</button>
    </div>
```

### Backend Processing
```python
@app.route('/translate_text', methods=['POST'])
def translate_text():
    try:
        text = request.json.get('text', '')
        language = request.json.get('language', 'asl')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Get translation with context
        translation = translator.translate(text, language)
        
        # Convert to video paths
        video_paths = text_to_sign(translation['signs'], language)
        
        return jsonify({
            'video_paths': video_paths,
            'expressions': translation['expressions'],
            'context': translation.get('context', {})
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Feedback System
```python
def save_feedback(original, correction):
    """Save feedback to both JSON and log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    feedback_entry = {
        "timestamp": timestamp,
        "original": original,
        "correction": correction
    }
    
    try:
        # Save to JSON and log files
        with open(FEEDBACK_FILE, 'a') as f:
            json.dump(feedback_entry, f)
        with open(FEEDBACK_LOG, 'a') as f:
            f.write(f'[{timestamp}] Original: "{original}" -> Correction: "{correction}"\n')
        return True
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return False
```

## Setup & Deployment

### Prerequisites
- Python 3.x
- Flask
- Vosk
- PyAudio
- Required AI models

### Installation Steps
```bash
# Clone repository
git clone [repository-url]

# Install dependencies
pip install -r requirements.txt

# Download AI models
# Place in VSTEST1/models/

# Run application
python app.py
```

### Running the Application
Access via:
- Local: http://127.0.0.1:5001
- Network: http://[your-ip]:5001

### Important Notes
1. Use HTTP instead of HTTPS
2. Ensure proper model installation
3. Check microphone permissions
4. Monitor feedback logs
5. Verify media files existence

## Testing

### Model Testing
```python
def test_model(language):
    """Test speech recognition for specific language"""
    model_path = MODEL_PATHS[language]
    
    try:
        model = Model(str(model_path))
        recognizer = KaldiRecognizer(model, 16000)
        print(f"Testing {language} recognition...")
        # Test recognition
    except Exception as e:
        print(f"Error testing {language} model: {str(e)}")
```

### Performance Monitoring
```python
def measure_performance():
    """
    Measures:
    - Recognition speed
    - Translation accuracy
    - Video playback smoothness
    """
    # Performance metrics implementation
```

## Security Features

### Video Protection
```javascript
// Prevent video downloads
video.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

// Disable keyboard controls
video.addEventListener('keydown', function(e) {
    e.preventDefault();
});
```

### Error Handling
```python
try:
    # Process request
    if not original or not correction:
        return jsonify({"status": False, "error": "Missing fields"})
except Exception as e:
    return jsonify({"status": False, "error": str(e)})
```

## Future Enhancements
1. Additional language support
2. Improved accuracy
3. Mobile application
4. Offline mode
5. Real-time video generation
6. Enhanced error handling
7. Better performance optimization
8. User preferences storage
``` 