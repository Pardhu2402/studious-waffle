import os
import sys
from pathlib import Path
from vosk import Model, KaldiRecognizer
import traceback
from textblob import TextBlob
import speech_recognition as sr
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import stat

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Check directory permissions on startup
def check_directory_permissions():
    # Use current working directory instead of hardcoded path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_path = os.path.join(current_dir, "uploads")
    print("\nChecking upload directory permissions:")
    print(f"Upload path: {upload_path}")
    
    # Check if directory exists
    if not os.path.exists(upload_path):
        try:
            os.makedirs(upload_path, mode=0o755)
            print("Created upload directory")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    
    # Check permissions
    try:
        # Get directory stats
        st = os.stat(upload_path)
        print(f"Directory permissions: {stat.filemode(st.st_mode)}")
        print(f"Owner: {st.st_uid}")
        print(f"Group: {st.st_gid}")
        
        # Check if writable
        if os.access(upload_path, os.W_OK):
            print("Directory is writable")
        else:
            print("Directory is not writable!")
            
        # Create test file
        test_file = os.path.join(upload_path, "test.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("Successfully created and removed test file")
        except Exception as e:
            print(f"Error testing write access: {e}")
            return False
            
        return True
    except Exception as e:
        print(f"Error checking permissions: {e}")
        return False

# Check directory permissions on startup
if not check_directory_permissions():
    print("Error: Upload directory is not properly configured!")
    sys.exit(1)

# Base project path and upload structure setup
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_PATH, "uploads")

# Derived paths
ALPHABET_IMAGES_PATH = os.path.join(PROJECT_PATH, "alphabetimages")
VIDEOS_PATH = os.path.join(PROJECT_PATH, "mp4videos")

# Model paths
VOSK_MODEL_PATH_ISL = os.path.join(PROJECT_PATH, "vosk-model-en-in-0.5")
VOSK_MODEL_PATH_ASL = os.path.join(PROJECT_PATH, "vosk-model-small-en-us-0.15")
VOSK_MODEL_PATH_HINDI = os.path.join(PROJECT_PATH, "vosk-model-small-hi-0.22")
VOSK_MODEL_PATH_TELUGU = os.path.join(PROJECT_PATH, "vosk-model-small-te-0.42")
VOSK_MODEL_PATH_GUJARATI = os.path.join(PROJECT_PATH, "vosk-model-small-gu-0.42")

# Indian alphabets path
INDIAN_ALPHABET_IMAGES_PATH = os.path.join(PROJECT_PATH, "indianalphabetsandnumbers")

# Common words that are similar across languages
common_signs = {
    'hello': 'hello.mp4',
    'thank_you': 'thank_you.mp4',
    'yes': 'yes.mp4',
    'no': 'no.mp4',
    'please': 'please.mp4',
    'sorry': 'sorry.mp4',
    'good': 'good.mp4',
    'bad': 'bad.mp4',
    'help': 'help.mp4',
    'want': 'want.mp4',
    'need': 'need.mp4',
    'understand': 'understand.mp4',
    'not_understand': 'not_understand.mp4',
}

# First, add the regional character mappings at the top of the file with other constants
regional_char_maps = {
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

# At the top of the file, add a function to scan available media files

def scan_available_media():
    """Scan and catalog all available video and image files"""
    videos = {}
    asl_images = {}
    isl_images = {}
    
    # Scan MP4 videos
    print("\nScanning available videos...")
    for file in os.listdir(VIDEOS_PATH):
        if file.endswith('.mp4'):
            base_name = file[:-4].lower()  # Remove .mp4 and convert to lowercase
            videos[base_name] = file
            print(f"Found video: {file}")
    
    # Scan ASL alphabet images
    print("\nScanning ASL alphabet images...")
    for file in os.listdir(ALPHABET_IMAGES_PATH):
        if file.endswith('_test.jpg'):
            base_name = file[:-9].lower()  # Remove _test.jpg and convert to lowercase
            asl_images[base_name] = file
            print(f"Found ASL image: {file}")
            
            # Also map uppercase version for special cases
            if base_name.upper() == base_name:
                asl_images[base_name.lower()] = file
    
    # Scan ISL alphabet images
    print("\nScanning ISL alphabet images...")
    for file in os.listdir(INDIAN_ALPHABET_IMAGES_PATH):
        if file.endswith('.jpg'):
            base_name = file[:-4].lower()  # Remove .jpg and convert to lowercase
            isl_images[base_name] = file
            print(f"Found ISL image: {file}")
            
            # Also map uppercase version for special cases
            if base_name.upper() == base_name:
                isl_images[base_name.lower()] = file
    
    # Add special mappings
    asl_images['space'] = 'space_test.jpg'
    asl_images['nothing'] = 'nothing_test.jpg'
    isl_images['space'] = 'space_test.jpg'
    isl_images['nothing'] = 'nothing_test.jpg'
    
    # Map all video files to both dictionaries
    for word, file in videos.items():
        if word.isupper():  # If filename is uppercase, map lowercase version too
            videos[word.lower()] = file
    
    print("\nTotal media files found:")
    print(f"Videos: {len(videos)}")
    print(f"ASL Images: {len(asl_images)}")
    print(f"ISL Images: {len(isl_images)}")
    
    return videos, asl_images, isl_images

# Scan available media files
AVAILABLE_VIDEOS, ASL_IMAGES, ISL_IMAGES = scan_available_media()

# Update dictionaries based on available files
video_dict = {
    # Common words across all languages
    'hello': 'hello.mp4',
    'thank': 'thank.mp4',
    'you': 'you.mp4',
    'yes': 'yes.mp4',
    'no': 'no.mp4',
    'please': 'please.mp4',
    'sorry': 'sorry.mp4',
    'good': 'good.mp4',
    'bad': 'bad.mp4',
    'help': 'help.mp4',
    'want': 'want.mp4',
    'need': 'need.mp4',
    'understand': 'understand.mp4',
    'not': 'not.mp4',
    'weather': 'weather.mp4',
    'rain': 'rain.mp4',
    'hot': 'hot.mp4',
    'cold': 'cold.mp4',
    'wind': 'wind.mp4',
    'sunny': 'sunny.mp4',
    'cloud': 'cloud.mp4',
    'storm': 'storm.mp4',
    # Add all available videos from scan
    **{word: path for word, path in AVAILABLE_VIDEOS.items()}
}

# ISL dictionary with all available videos
isl_video_dict = {
    # Common words
    'hello': 'hello.mp4',
    'thank': 'thank.mp4',
    'you': 'you.mp4',
    'yes': 'yes.mp4',
    'no': 'no.mp4',
    'please': 'please.mp4',
    'sorry': 'sorry.mp4',
    'good': 'good.mp4',
    'bad': 'bad.mp4',
    'help': 'help.mp4',
    'want': 'want.mp4',
    'need': 'need.mp4',
    'understand': 'understand.mp4',
    'not': 'not.mp4',
    
    # Weather terms
    'weather': 'weather.mp4',
    'rain': 'rain.mp4',
    'hot': 'hot.mp4',
    'cold': 'cold.mp4',
    'wind': 'wind.mp4',
    'sunny': 'sunny.mp4',
    'cloud': 'cloud.mp4',
    'storm': 'storm.mp4',
    
    # ISL specific words
    'namaste': 'namaste.mp4',
    'dhanyavaad': 'thank.mp4',
    'haan': 'yes.mp4',
    'nahi': 'no.mp4',
    'kripya': 'please.mp4',
    'maaf': 'sorry.mp4',
    'accha': 'good.mp4',
    'bura': 'bad.mp4',
    'madad': 'help.mp4',
    'chahiye': 'want.mp4',
    'samajh': 'understand.mp4',
    
    # Weather terms in Hindi/ISL
    'mausam': 'weather.mp4',
    'baarish': 'rain.mp4',
    'garmi': 'hot.mp4',
    'thandi': 'cold.mp4',
    'hawa': 'wind.mp4',
    'dhoop': 'sunny.mp4',
    'badal': 'cloud.mp4',
    'toofan': 'storm.mp4'
}

# Regional mappings to ISL words
regional_to_isl = {
    # Hindi mappings
    'नमस्ते': 'namaste',
    'धन्यवाद': 'dhanyavaad',
    'हाँ': 'haan',
    'नहीं': 'nahi',
    'कृपया': 'kripya',
    'माफ़': 'maaf',
    'अच्छा': 'accha',
    'बुरा': 'bura',
    'मदद': 'madad',
    'चाहिए': 'chahiye',
    'समझ': 'samajh',
    'मौसम': 'mausam',
    'बारिश': 'baarish',
    'गरमी': 'garmi',
    'ठंडी': 'thandi',
    'हवा': 'hawa',
    'धूप': 'dhoop',
    'बादल': 'badal',
    'तूफान': 'toofan',
    
    # Telugu mappings
    'నమస్కారం': 'namaste',
    'ధన్యవాదాలు': 'dhanyavaad',
    'అవును': 'haan',
    'కాదు': 'nahi',
    'దయచేసి': 'kripya',
    'క్షమించండి': 'maaf',
    'మంచి': 'accha',
    'చెడ్డ': 'bura',
    'సహాయం': 'madad',
    'కావాలి': 'chahiye',
    'అర్థం': 'samajh',
    'వాతావరణం': 'mausam',
    'వర్షం': 'baarish',
    'వేడి': 'garmi',
    'చల్లని': 'thandi',
    'గాలి': 'hawa',
    'మేఘం': 'dhoop',
    'మేఘాలు': 'badal',
    'తుఫాను': 'toofan',
    
    # Gujarati mappings
    'નમસ્તે': 'namaste',
    'આભાર': 'dhanyavaad',
    'હા': 'haan',
    'ના': 'nahi',
    'કૃપા': 'kripya',
    'માફ': 'maaf',
    'સારું': 'accha',
    'ખરાબ': 'bura',
    'મદદ': 'madad',
    'જોઈએ': 'chahiye',
    'સમજ': 'samajh',
    'હવામાન': 'mausam',
    'વરસાદ': 'baarish',
    'ગરમ': 'garmi',
    'ઠંડું': 'thandi',
    'પવન': 'hawa',
    'તડકો': 'dhoop',
    'વાદળ': 'badal',
    'તોફાન': 'toofan'
}

# Hindi video dictionary
hindi_video_dict = {
    # Weather terms
    'मौसम': 'weather.mp4',
    'गरम': 'hot.mp4',
    'ठंडा': 'cold.mp4',
    'बारिश': 'rain.mp4',
    'भारी बारिश': 'heavy rain.mp4',
    'बिजली': 'lightning.mp4',
    'बादल': 'cloudy.mp4',
    'धूप': 'sunny.mp4',
    'बर्फ': 'snow.mp4',
    'ओला': 'hail.mp4',
    'गरज': 'thunder.mp4',
    'धुंध': 'smog.mp4',
    'नम': 'humid.mp4',
    'हवा': 'windy.mp4',
    'हल्की हवा': 'breezy.mp4',
    
    # Time
    'आज': 'today.mp4',
    'सुबह': 'morning.mp4',
    'दोपहर': 'afternoon.mp4',
    'शाम': 'evening.mp4',
    'रात': 'night.mp4',
    'देर': 'late.mp4',
    'जल्दी': 'early.mp4',
    'समय': 'time.mp4',
    'दिन': 'day.mp4',
    'घंटा': 'hour.mp4',
    'मिनट': 'minute.mp4',
    
    # Days
    'सोमवार': 'monday.mp4',
    'मंगलवार': 'tuesday.mp4',
    'बुधवार': 'wednesday.mp4',
    'गुरुवार': 'thursday.mp4',
    'शुक्रवार': 'friday.mp4',
    'शनिवार': 'saturday.mp4',
    'रविवार': 'sunday.mp4',
    'सप्ताहांत': 'weekend.mp4',
    'हर सोमवार': 'every monday.mp4',
    'हर मंगलवार': 'every tuesday.mp4',
    'हर बुधवार': 'every wednesday.mp4',
    'हर गुरुवार': 'every thursday.mp4',
    'हर शुक्रवार': 'every friday.mp4',
    'हर सप्ताह': 'every week.mp4',
    'अगला सप्ताह': 'next week.mp4',
    
    # Months
    'जनवरी': 'january.mp4',
    'फरवरी': 'february.mp4',
    'मार्च': 'march.mp4',
    'अप्रैल': 'april.mp4',
    'जुलाई': 'july.mp4',
    'नवंबर': 'november.mp4',
    'दिसंबर': 'december.mp4',
    
    # Seasons
    'वसंत': 'spring.mp4',
    'गर्मी': 'summer.mp4',
    'सर्दी': 'winter.mp4',
    
    # Pronouns
    'मैं': 'i.mp4',
    'मुझे': 'me.mp4',
    'हम': 'we.mp4',
    'हमें': 'us.mp4',
    'यह': 'it.mp4',
    'वह': 'he.mp4',
    'उसको': 'him.mp4',
    'वे': 'they.mp4',
    'उन्हें': 'them.mp4',
    'स्वयं': 'myself.mp4',
    'खुद': 'yourself.mp4',
    'अपने आप': 'himself.mp4',
    'उसकी': 'her.mp4',
    'उनका': 'their.mp4',
    'हमारा': 'our.mp4',
    'मेरा': 'my.mp4'
}

# Update regional_to_isl with all mappings
regional_to_isl.update({
    # Add Hindi mappings
    'मैं': 'i',
    'मुझे': 'me',
    'हम': 'we',
    'हमें': 'us',
    'यह': 'it',
    'वह': 'he',
    'उसको': 'him',
    'वे': 'they',
    'उन्हें': 'them',
    'स्वयं': 'myself',
    'खुद': 'yourself',
    'अपने आप': 'himself',
    'उसकी': 'her',
    'उनका': 'their',
    'हमारा': 'our',
    'मेरा': 'my',
    'सोमवार': 'monday',
    'मंगलवार': 'tuesday',
    'बुधवार': 'wednesday',
    'गुरुवार': 'thursday',
    'शुक्रवार': 'friday',
    'शनिवार': 'saturday',
    'रविवार': 'sunday',
    
    # Add Telugu mappings from telugu_video_dict
    'వాతావరణం': 'weather',
    'వేడి': 'hot',
    'చల్లని': 'cold',
    'వర్షం': 'rain',
    'భారీ వర్షం': 'heavy_rain',
    'మెరుపు': 'lightning',
    'మేఘాలు': 'cloudy',
    'ఎండ': 'sunny',
    'మంచు': 'snow',
    'వడగళ్ళు': 'hail',
    'ఉరుము': 'thunder',
    
    # Add Gujarati mappings from gujarati_video_dict
    'હવામાન': 'weather',
    'ગરમ': 'hot',
    'ઠંડું': 'cold',
    'વરસાદ': 'rain',
    'ભારે વરસાદ': 'heavy_rain',
    'વીજળી': 'lightning',
    'વાદળછાયું': 'cloudy',
    'તડકો': 'sunny',
    'બરફ': 'snow',
    'કરા': 'hail',
    'ગડગડાટ': 'thunder'
})

# Add these to hindi_video_dict
hindi_video_dict.update({
    # Common Hindi words and phrases
    'अगर': 'if.mp4',
    'विश्राम': 'rest.mp4',
    'करते': 'doing.mp4',
    'तो': 'then.mp4',
    'गंतव्य': 'destination.mp4',
    'स्थल': 'place.mp4',
    'पर': 'on.mp4',
    'पहुंचे': 'reach.mp4',
    
    # More common Hindi words
    'और': 'and.mp4',
    'में': 'in.mp4',
    'है': 'is.mp4',
    'था': 'was.mp4',
    'के': 'of.mp4',
    'लिए': 'for.mp4',
    'से': 'from.mp4',
    'को': 'to.mp4',
    'एक': 'one.mp4',
    'यह': 'this.mp4',
    'वह': 'that.mp4',
    'जो': 'who.mp4',
    'सब': 'all.mp4',
    'कुछ': 'some.mp4',
    'होगा': 'will.mp4',
    'करना': 'do.mp4',
    'जाना': 'go.mp4',
    'आना': 'come.mp4'
})

# Update regional_to_isl mappings
regional_to_isl.update({
    'अगर': 'if',
    'विश्राम': 'rest',
    'करते': 'doing',
    'तो': 'then',
    'गंतव्य': 'destination',
    'स्थल': 'place',
    'पर': 'on',
    'पहुंचे': 'reach'
})

# Remove the automatic model loading and verification at import
# Instead, just define the functions

def load_model(language):
    """Load speech recognition model for specified language"""
    try:
        model_paths = {
            'isl': VOSK_MODEL_PATH_ISL,
            'asl': VOSK_MODEL_PATH_ASL,
            'hindi': VOSK_MODEL_PATH_HINDI,
            'telugu': VOSK_MODEL_PATH_TELUGU,
            'gujarati': VOSK_MODEL_PATH_GUJARATI
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

def verify_models():
    """Verify model existence and print detailed status"""
    models = {
        'ASL': VOSK_MODEL_PATH_ASL,
        'ISL': VOSK_MODEL_PATH_ISL,
        'Hindi': VOSK_MODEL_PATH_HINDI,
        'Telugu': VOSK_MODEL_PATH_TELUGU,
        'Gujarati': VOSK_MODEL_PATH_GUJARATI
    }
    
    missing_models = []
    
    print("\nVerifying speech recognition models:")
    print("=" * 50)
    
    for name, path in models.items():
        print(f"\nChecking {name} model:")
        print(f"Path: {path}")
        
        if not os.path.exists(path):
            print(f"❌ {name} model directory not found")
            missing_models.append(name)
            continue
            
        # Check required directories and key files
        required_items = [
            'am',
            'conf',
            'graph',
            'ivector',
            'graph/phones/word_boundary.int'  # This is a key file we know exists
        ]
        
        missing_items = []
        for item in required_items:
            full_path = os.path.join(path, item)
            if not os.path.exists(full_path):
                missing_items.append(item)
        
        if missing_items:
            print(f"❌ {name} model is missing required items:")
            for item in missing_items:
                print(f"  - {item}")
            missing_models.append(name)
        else:
            print(f"✓ {name} model is complete and ready")
            print(f"  Found all required components:")
            for item in required_items:
                print(f"  - {item}")
    
    if missing_models:
        print("\nMissing or incomplete models:")
        for model in missing_models:
            print(f"- {model}")
    else:
        print("\nAll models are properly installed!")
    
    return missing_models

# Store missing models without trying to load them
MISSING_MODELS = verify_models()

def inspect_model_paths():
    """Inspect and print the contents of model directories"""
    models = {
        'ASL': VOSK_MODEL_PATH_ASL,
        'ISL': VOSK_MODEL_PATH_ISL,
        'Hindi': VOSK_MODEL_PATH_HINDI,
        'Telugu': VOSK_MODEL_PATH_TELUGU,
        'Gujarati': VOSK_MODEL_PATH_GUJARATI
    }
    
    print("\nInspecting model directories:")
    print("=" * 50)
    
    for name, path in models.items():
        print(f"\n{name} Model:")
        print(f"Path: {path}")
        
        if os.path.exists(path):
            print("Directory contents:")
            for root, dirs, files in os.walk(path):
                level = root.replace(path, '').count(os.sep)
                indent = ' ' * 4 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 4 * (level + 1)
                for f in files:
                    print(f"{subindent}{f}")
        else:
            print("❌ Directory not found")
            
    print("\n" + "=" * 50)

# Call the inspection function
inspect_model_paths()

def text_to_sign(signs, language='asl'):
    """Convert text to sign language video paths"""
    video_paths = []
    
    try:
        print(f"\nChecking directories:")
        print(f"ASL Path: {ALPHABET_IMAGES_PATH}")
        print(f"ISL Path: {INDIAN_ALPHABET_IMAGES_PATH}")
        print(f"Videos Path: {VIDEOS_PATH}")
        
        # Verify directories exist
        if not os.path.exists(ALPHABET_IMAGES_PATH):
            print(f"Warning: ASL directory does not exist!")
            return []
        if not os.path.exists(INDIAN_ALPHABET_IMAGES_PATH):
            print(f"Warning: ISL directory does not exist!")
            return []
        if not os.path.exists(VIDEOS_PATH):
            print(f"Warning: Videos directory does not exist!")
            return []
            
        # Scan available files
        asl_files = set(os.listdir(ALPHABET_IMAGES_PATH))
        isl_files = set(os.listdir(INDIAN_ALPHABET_IMAGES_PATH))
        video_files = set(os.listdir(VIDEOS_PATH))
        
        print(f"\nFound files:")
        print(f"ASL files: {len(asl_files)}")
        print(f"ISL files: {len(isl_files)}")
        print(f"Video files: {len(video_files)}")
        
    except Exception as e:
        print(f"Error scanning directories: {e}")
        traceback.print_exc()
        return []

    try:
        # First check if this is a regional language or ISL
        is_regional = language.lower() in ['hindi', 'telugu', 'gujarati', 'isl']
        
        if is_regional or language.lower() == 'isl':
            # ISL and regional language handling
            # Create English to ISL character mapping (uppercase to match actual files)
            english_to_isl = {
                'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E',
                'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J',
                'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'o': 'O',
                'p': 'P', 'q': 'Q', 'r': 'R', 's': 'S', 't': 'T',
                'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X', 'y': 'Y', 'z': 'Z'
            }
            
            # Select appropriate dictionary and character map
            video_dict_to_use = isl_video_dict
            char_map = regional_char_maps.get(language.lower(), {})
            
            # Map words through regional_to_isl dictionary
            mapped_words = []
            for word in signs.split():
                if word in regional_to_isl:
                    mapped_word = regional_to_isl[word]
                    print(f"Mapped '{word}' to '{mapped_word}'")
                    mapped_words.append(mapped_word)
                else:
                    mapped_words.append(word)
            
            words = mapped_words

            print(f"\nProcessing text in {language.upper()}: {words}")
            
            for word in words:
                if not word or word.isspace():
                    continue
                    
                original_word = word.lower()
                print(f"Processing word: '{original_word}'")
                
                # Try video matches first
                video_found = False
                
                # Try video matches (common signs, dictionary, direct MP4)
                if original_word in common_signs:
                    video_path = common_signs[original_word]
                    if os.path.exists(os.path.join(VIDEOS_PATH, video_path)):
                        video_paths.append(f"mp4videos/{video_path}")
                        print(f"Found common video for: {original_word}")
                        video_found = True
                        continue

                if not video_found and original_word in video_dict_to_use:
                    video_path = video_dict_to_use[original_word]
                    if os.path.exists(os.path.join(VIDEOS_PATH, video_path)):
                        video_paths.append(f"mp4videos/{video_path}")
                        print(f"Found video for: {original_word}")
                        video_found = True
                        continue

                direct_video = f"{original_word}.mp4"
                if not video_found and os.path.exists(os.path.join(VIDEOS_PATH, direct_video)):
                    video_paths.append(f"mp4videos/{direct_video}")
                    print(f"Found direct video match for: {original_word}")
                    video_found = True
                    continue

                # If no video found, spell using ISL alphabet images
                if not video_found:
                    print(f"No video found, spelling word: {word}")
                    has_letters = False
                    
                    # For ISL/regional, spell using Indian alphabet images
                    for char in word:
                        if is_regional and char in char_map:
                            # Use mapped character for regional scripts
                            mapped_char = char_map[char].upper()  # Convert to uppercase
                            if mapped_char:  # Skip empty mappings (like halant)
                                char_file = f"{mapped_char}.jpg"
                                if char_file in isl_files:
                                    has_letters = True
                                    video_paths.append(f"indianalphabetsandnumbers/{char_file}")
                                    print(f"Added mapped ISL character: {mapped_char}")
                                    continue
                                else:
                                    print(f"No ISL image found for mapped character: {mapped_char}")
                        elif char.isalpha():
                            # For English characters or ISL
                            char_upper = char.upper()
                            char_file = f"{char_upper}.jpg"
                            if char_file in isl_files:
                                has_letters = True
                                video_paths.append(f"indianalphabetsandnumbers/{char_file}")
                                print(f"Added ISL character: {char_upper}")
                                continue
                            else:
                                print(f"No ISL image found for character: {char}")
                        elif char.isdigit():
                            num_file = f"{char}.jpg"
                            if num_file in isl_files:
                                has_letters = True
                                video_paths.append(f"indianalphabetsandnumbers/{num_file}")
                                print(f"Added ISL number: {char}")
                                continue
                            else:
                                print(f"No ISL image found for number: {char}")
                        else:
                            print(f"Skipping character: {char}")
                    
                    # Add space after spelled words
                    if has_letters:
                        space_file = "SPACE.jpg"
                        if space_file in isl_files:
                            video_paths.append(f"indianalphabetsandnumbers/{space_file}")

        else:  # ASL handling
            video_dict_to_use = video_dict
            words = signs.split() if isinstance(signs, str) else signs

            print(f"\nProcessing text in ASL: {words}")
            
            for word in words:
                if not word or word.isspace():
                    continue
                    
                original_word = word.lower()
                print(f"Processing word: '{original_word}'")
                
                # Try video matches first
                video_found = False
                
                # Try video matches (common signs, dictionary, direct MP4)
                if original_word in common_signs:
                    video_path = common_signs[original_word]
                    if os.path.exists(os.path.join(VIDEOS_PATH, video_path)):
                        video_paths.append(f"mp4videos/{video_path}")
                        print(f"Found common video for: {original_word}")
                        video_found = True
                        continue

                if not video_found and original_word in video_dict_to_use:
                    video_path = video_dict_to_use[original_word]
                    if os.path.exists(os.path.join(VIDEOS_PATH, video_path)):
                        video_paths.append(f"mp4videos/{video_path}")
                        print(f"Found video for: {original_word}")
                        video_found = True
                        continue

                direct_video = f"{original_word}.mp4"
                if not video_found and os.path.exists(os.path.join(VIDEOS_PATH, direct_video)):
                    video_paths.append(f"mp4videos/{direct_video}")
                    print(f"Found direct video match for: {original_word}")
                    video_found = True
                    continue

                # If no video found, spell using ASL alphabet images
                if not video_found:
                    print(f"No video found, spelling word: {word}")
                    has_letters = False
                    
                    # For ASL, spell using alphabet images
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
                        else:
                            print(f"Skipping character: {char}")
                    
                    # Add space after spelled words
                    if has_letters:
                        space_file = "SPACE_test.jpg"
                        if space_file in asl_files:
                            video_paths.append(f"alphabetimages/{space_file}")

        if video_paths:
            print(f"Generated {len(video_paths)} video paths")
            print("Paths:", video_paths)
            return video_paths
        else:
            print("No signs found for the given text")
            # Return a "not found" or "error" sign if available
            error_sign = "not_understand.mp4"
            if os.path.exists(os.path.join(VIDEOS_PATH, error_sign)):
                return [f"mp4videos/{error_sign}"]
            return []
            
    except Exception as e:
        print(f"Error in text_to_sign: {e}")
        traceback.print_exc()
        return []

# Update the regional dictionaries with complete mappings

# Telugu video dictionary
telugu_video_dict = {
    # Weather
    'వాతావరణం': 'weather.mp4',
    'వేడి': 'hot.mp4',
    'చల్లని': 'cold.mp4',
    'వర్షం': 'rain.mp4',
    'భారీ వర్షం': 'heavy rain.mp4',
    'మెరుపు': 'lightning.mp4',
    'మేఘాలు': 'cloudy.mp4',
    'ఎండ': 'sunny.mp4',
    'మంచు': 'snow.mp4',
    'వడగళ్ళు': 'hail.mp4',
    'ఉరుము': 'thunder.mp4',
    'పొగమంచు': 'smog.mp4',
    'తేమ': 'humid.mp4',
    'గాలి': 'windy.mp4',
    'చల్లని గాలి': 'breezy.mp4',
    'దుమారం': 'dust storm.mp4',
    'నల్ల మంచు': 'black ice.mp4',
    'నిర్మల ఆకాశం': 'clear skies.mp4',
    'చెదురుమదురు వర్షం': 'scattered rain.mp4',
    'చెదురుమదురు మంచు': 'scattered snow.mp4',
    'కుండపోత వర్షం': 'pouring rain.mp4',
    'వేడి గాలులు': 'heat wave.mp4',
    'మంచు తుఫాను': 'blizzard.mp4',
    'మంచు బిందువులు': 'morning dew.mp4',
    'ఇంద్రధనుస్సు': 'rainbow.mp4',
    'పొడి': 'dry.mp4',
    'చురుకైన': 'brisk.mp4',
    'జారుడు': 'slippery.mp4',

    # Time
    'ఈరోజు': 'today.mp4',
    'ఉదయం': 'morning.mp4',
    'మధ్యాహ్నం': 'afternoon.mp4',
    'సాయంత్రం': 'evening.mp4',
    'రాత్రి': 'night.mp4',
    'ఆలస్యం': 'late.mp4',
    'ముందుగా': 'early.mp4',
    'సమయం': 'time.mp4',
    'రోజు': 'day.mp4',
    'గంట': 'hour.mp4',
    'నిమిషం': 'minute.mp4',
    'తెల్లవారు': 'dawn.mp4',
    'సంధ్య': 'dusk.mp4',
    'మధ్యాహ్నం': 'noon.mp4',
    'అర్ధరాత్రి': 'midnight.mp4',
    'రాత్రి పొద్దు': 'late night.mp4',
    'సూర్యోదయం': 'sunrise.mp4',
    'సూర్యాస్తమయం': 'sunset.mp4',

    # Days
    'సోమవారం': 'monday.mp4',
    'మంగళవారం': 'tuesday.mp4',
    'బుధవారం': 'wednesday.mp4',
    'గురువారం': 'thursday.mp4',
    'శుక్రవారం': 'friday.mp4',
    'ఆదివారం': 'sunday.mp4',
    'వారాంతం': 'weekend.mp4',
    'ప్రతి సోమవారం': 'every monday.mp4',
    'ప్రతి మంగళవారం': 'every tuesday.mp4',
    'ప్రతి బుధవారం': 'every wednesday.mp4',
    'ప్రతి గురువారం': 'every thursday.mp4',
    'ప్రతి శుక్రవారం': 'every friday.mp4',
    'ప్రతి వారం': 'every week.mp4',
    'వచ్చే వారం': 'next week.mp4'
}

# Gujarati video dictionary
gujarati_video_dict = {
    # Weather
    'હવામાન': 'weather.mp4',
    'ગરમ': 'hot.mp4',
    'ઠંડું': 'cold.mp4',
    'વરસાદ': 'rain.mp4',
    'ભારે વરસાદ': 'heavy rain.mp4',
    'વીજળી': 'lightning.mp4',
    'વાદળછાયું': 'cloudy.mp4',
    'તડકો': 'sunny.mp4',
    'બરફ': 'snow.mp4',
    'કરા': 'hail.mp4',
    'ગડગડાટ': 'thunder.mp4',
    'ધુમ્મસ': 'smog.mp4',
    'ભેજવાળું': 'humid.mp4',
    'પવન': 'windy.mp4',
    'મંદ પવન': 'breezy.mp4',
    'ધૂળની આંધી': 'dust storm.mp4',
    'કાળો બરફ': 'black ice.mp4',
    'ચોખ્ખું આકાશ': 'clear skies.mp4',
    'છૂટોછવાયો વરસાદ': 'scattered rain.mp4',
    'છૂટોછવાયો બરફ': 'scattered snow.mp4',
    'ધોધમાર વરસાદ': 'pouring rain.mp4',
    'ગરમીનું મોજું': 'heat wave.mp4',
    'બરફનું તોફાન': 'blizzard.mp4',
    'ઝાકળ': 'morning dew.mp4',
    'મેઘધનુષ': 'rainbow.mp4',
    'સૂકું': 'dry.mp4',
    'ઝડપી': 'brisk.mp4',
    'લપસણું': 'slippery.mp4',

    # Time
    'આજે': 'today.mp4',
    'સવાર': 'morning.mp4',
    'બપોર': 'afternoon.mp4',
    'સાંજ': 'evening.mp4',
    'રાત': 'night.mp4',
    'મોડું': 'late.mp4',
    'વહેલું': 'early.mp4',
    'સમય': 'time.mp4',
    'દિવસ': 'day.mp4',
    'કલાક': 'hour.mp4',
    'મિનિટ': 'minute.mp4',
    'પરોઢ': 'dawn.mp4',
    'સંધ્યા': 'dusk.mp4',
    'બપોર': 'noon.mp4',
    'મધરાત': 'midnight.mp4',
    'મોડી રાત': 'late night.mp4',
    'સూર્યોદય': 'sunrise.mp4',
    'સూર્યાસ્ત': 'sunset.mp4',

    # Days
    'સોમવાર': 'monday.mp4',
    'મંગળવાર': 'tuesday.mp4',
    'બુધવાર': 'wednesday.mp4',
    'ગુરુવાર': 'thursday.mp4',
    'శુక్రవారం': 'friday.mp4',
    'રવિવાર': 'sunday.mp4',
    'સપ્તાહાંત': 'weekend.mp4',
    'દર સોમવારે': 'every monday.mp4',
    'દર મંગળવારે': 'every tuesday.mp4',
    'દર બુધવારે': 'every wednesday.mp4',
    'દર ગુરુવારે': 'every thursday.mp4',
    'દર శుక్రవారే': 'every friday.mp4',
    'દર અઠવાડિયે': 'every week.mp4',
    'આવતા અઠવાડિયે': 'next week.mp4'
}

# Update Hindi dictionary with all mappings
hindi_video_dict.update({
    # Additional time words
    'हर मंगलवार': 'every tuesday.mp4',
    'हर बुधवार': 'every wednesday.mp4',
    'हर गुरुवार': 'every thursday.mp4',
    'हर शुक्रवार': 'every friday.mp4',
    'हर सप्ताह': 'every week.mp4',
    'अगला सप्ताह': 'next week.mp4',

    # Additional months
    'जनवरी': 'january.mp4',
    'फरवरी': 'february.mp4',
    'मार्च': 'march.mp4',
    'अप्रैल': 'april.mp4',
    'जुलाई': 'july.mp4',
    'नवंबर': 'november.mp4',
    'दिसंबर': 'december.mp4',

    # Additional seasons
    'वसंत': 'spring.mp4',
    'गर्मी': 'summer.mp4',
    'सर्दी': 'wintering.mp4',

    # Additional pronouns
    'हम सब': 'ourselves.mp4',
    'स्वयं': 'itself.mp4',
    'खुद': 'herself.mp4'
})

# Update regional_to_isl with additional mappings
regional_to_isl.update({
    # Add all the mappings from the dictionaries above
    # This ensures words are properly mapped to ISL signs
})

def verify_telugu_model():
    """Verify Telugu model specifically"""
    print("\nVerifying Telugu speech recognition model:")
    print("=" * 50)
    
    if not os.path.exists(VOSK_MODEL_PATH_TELUGU):
        print("❌ Telugu model directory not found")
        return False
        
    required_items = [
        'am',
        'conf',
        'graph',
        'ivector',
        'graph/phones/word_boundary.int',
        'graph/words.txt',  # Telugu words list
        'graph/phones.txt'  # Telugu phones list
    ]
    
    for item in required_items:
        full_path = os.path.join(VOSK_MODEL_PATH_TELUGU, item)
        if not os.path.exists(full_path):
            print(f"❌ Telugu model missing: {item}")
            return False
    
    print("✓ Telugu model is complete and ready")
    return True

def analyze_sentiment(text):
    analysis = TextBlob(text)
    # Get polarity score (-1 to 1, where -1 is negative, 0 is neutral, 1 is positive)
    polarity = analysis.sentiment.polarity
    
    # Determine sentiment category
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # Get the audio file from the request
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'})
    
    audio_file = request.files['audio']
    
    try:
        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            
        # Get the transcribed text
        text = recognizer.recognize_google(audio)
        
        # Add sentiment analysis
        sentiment = analyze_sentiment(text)
        
        # Convert text to sign language paths
        sign_paths = text_to_sign(text)
        
        return jsonify({
            'text': text,
            'sentiment': sentiment,
            'sign_paths': sign_paths
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# Add these constants at the top with your other constants
UPLOAD_FOLDER = os.path.join(PROJECT_PATH, "uploads")
ALLOWED_EXTENSIONS = {'mp4', 'jpg', 'jpeg', 'png'}  # Add image formats

# Create upload directory structure
def initialize_upload_directories():
    try:
        # Create main uploads directory
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        print(f"\nCreated main upload directory: {UPLOAD_FOLDER}")
        
        # Create language-specific directories
        languages = ['asl', 'isl', 'hindi', 'telugu', 'gujarati']
        for lang in languages:
            lang_dir = os.path.join(UPLOAD_FOLDER, lang)
            os.makedirs(lang_dir, exist_ok=True)
            print(f"Created language directory: {lang_dir}")
        
        # Create and initialize log file
        log_file = os.path.join(UPLOAD_FOLDER, 'uploads.log')
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("Upload Log File Created\n")
            print(f"Created upload log file: {log_file}")
            
        # Verify permissions
        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            os.chmod(root, 0o755)  # rwxr-xr-x
            print(f"Set permissions for: {root}")
            
        print("\nUpload directory structure initialized successfully!")
        return True
        
    except Exception as e:
        print(f"\nError initializing upload directories: {str(e)}")
        return False

# Initialize directories when the app starts
if not initialize_upload_directories():
    print("Failed to initialize upload directories. Exiting.")
    sys.exit(1)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_sign', methods=['POST'])
def upload_sign():
    try:
        # Use current directory for uploads
        current_dir = os.path.dirname(os.path.abspath(__file__))
        upload_path = os.path.join(current_dir, "uploads")
        print("\nDebug: Starting file upload...")
        print(f"Upload folder path: {upload_path}")
        
        if 'file' not in request.files:  # Changed from 'video' to 'file'
            print("Debug: No file in request")
            return jsonify({'error': 'No file provided'}), 400
            
        uploaded_file = request.files['file']  # Changed from video to file
        if not uploaded_file.filename:
            return jsonify({'error': 'No file selected'}), 400
            
        word = request.form.get('word', '').lower()
        language = request.form.get('language', '')
        file_type = request.form.get('type', 'video')  # Add file type parameter
        
        print(f"Debug: Received upload - Word: {word}, Language: {language}, Type: {file_type}")
        
        # Check file extension
        file_ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return jsonify({'error': 'Invalid file type. Allowed types: mp4, jpg, jpeg, png'}), 400
        
        # Create language directory
        language_dir = os.path.join(upload_path, language)
        os.makedirs(language_dir, exist_ok=True)
        
        # Save file with appropriate extension
        filename = secure_filename(f"{word}.{file_ext}")
        filepath = os.path.join(language_dir, filename)
        print(f"Saving to: {filepath}")
        
        uploaded_file.save(filepath)
        
        if os.path.exists(filepath):
            print(f"File saved successfully: {filepath}")
            # Log the upload
            log_path = os.path.join(upload_path, 'uploads.log')
            with open(log_path, 'a') as f:
                f.write(f"Uploaded: {language}/{filename} - Type: {file_type}\n")
            
            return jsonify({
                'success': True,
                'message': 'Upload successful',
                'path': filepath
            })
        else:
            print("File not saved!")
            return jsonify({'error': 'Failed to save file'}), 500
            
    except Exception as e:
        print(f"Upload error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/check_upload_dirs', methods=['GET'])
def check_upload_dirs():
    try:
        structure = {}
        print(f"\nChecking upload directory structure...")
        print(f"Base upload folder: {UPLOAD_FOLDER}")
        
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({'error': 'Upload folder does not exist'}), 404
            
        for language in ['asl', 'isl', 'hindi', 'telugu', 'gujarati']:
            lang_dir = os.path.join(UPLOAD_FOLDER, language)
            print(f"Checking {language} directory: {lang_dir}")
            
            if os.path.exists(lang_dir):
                files = os.listdir(lang_dir)
                structure[language] = {
                    'path': lang_dir,
                    'exists': True,
                    'files': files,
                    'writable': os.access(lang_dir, os.W_OK)
                }
            else:
                structure[language] = {
                    'path': lang_dir,
                    'exists': False,
                    'files': [],
                    'writable': False
                }
                
        # Check log file
        log_path = os.path.join(UPLOAD_FOLDER, 'uploads.log')
        structure['log'] = {
            'path': log_path,
            'exists': os.path.exists(log_path),
            'writable': os.access(os.path.dirname(log_path), os.W_OK) if os.path.exists(log_path) else False
        }
        
        return jsonify(structure)
    except Exception as e:
        print(f"Error checking directories: {str(e)}")
        return jsonify({'error': str(e)}), 500
