import os
import urllib.request
import zipfile
import shutil

def setup_models():
    # Use the direct paths where models should be located
    PROJECT_PATH = r"/Users/sreemadhav/SreeMadhav/prototype1 toshiba/Prototype1signl/VSTEST1"
    
    # Model URLs and their target directories
    model_urls = {
        'ASL': ('https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip', 
                os.path.join(PROJECT_PATH, "vosk-model-small-en-us-0.15")),
        'ISL': ('https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip',
                os.path.join(PROJECT_PATH, "vosk-model-en-in-0.5")),
        'Hindi': ('https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip',
                 os.path.join(PROJECT_PATH, "vosk-model-small-hi-0.22")),
        'Telugu': ('https://alphacephei.com/vosk/models/vosk-model-small-te-0.42.zip',
                  os.path.join(PROJECT_PATH, "vosk-model-small-te-0.42")),
        'Gujarati': ('https://alphacephei.com/vosk/models/vosk-model-small-gu-0.42.zip',
                    os.path.join(PROJECT_PATH, "vosk-model-small-gu-0.42"))
    }
    
    for language, (url, target_path) in model_urls.items():
        if os.path.exists(target_path):
            print(f"\n{language} model already exists at {target_path}")
            continue
            
        print(f"\nDownloading {language} model...")
        zip_path = os.path.join(PROJECT_PATH, f"{language.lower()}_model.zip")
        
        try:
            # Download model
            urllib.request.urlretrieve(url, zip_path)
            
            # Extract model
            print(f"Extracting {language} model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(PROJECT_PATH)
            
            # Clean up zip file
            os.remove(zip_path)
            print(f"{language} model installed successfully")
            
        except Exception as e:
            print(f"Error installing {language} model: {str(e)}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    print("\nModel setup completed!")

if __name__ == "__main__":
    setup_models() 