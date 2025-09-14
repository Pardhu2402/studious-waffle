# Sign Language Translator

A comprehensive web application that translates voice and text into sign language, supporting multiple languages including American Sign Language (ASL), Indian Sign Language (ISL), and regional Indian languages.

## Features

### Core Functionality
- Voice-to-Sign Language Translation
- Text-to-Sign Language Translation
- Real-time Translation Support
- Sentiment Analysis of Speech/Text
- Adjustable Playback Speed
- Multi-language Support

### Supported Languages
- American Sign Language (ASL)
- Indian Sign Language (ISL)
- Hindi Sign Language
- Telugu Sign Language
- Gujarati Sign Language

### Additional Features
- User-contributed Sign Upload System
- Comprehensive Learning Resources
- User Feedback System
- Sentiment Analysis Display
- Interactive UI with Live Status Updates

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Speech Recognition**: Vosk Models
- **Sentiment Analysis**: TextBlob
- **Media Processing**: Video.js

## Installation

1. Clone the repository:
2. 2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Download required Vosk models for speech recognition (not included in repository)

4. Set up the directory structure:
```
VSTEST1/
├── mp4videos/        # Sign language videos
├── alphabetimages/   # ASL alphabet images
├── uploads/          # User uploaded content
├── static/
│   ├── css/
│   └── js/
└── templates/
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Access the application at `http://localhost:5000`

3. Select your preferred sign language

4. Use either:
   - Text input for translation
   - Voice input for real-time translation

## Contributing

### Adding New Signs
1. Use the upload feature in the application
2. Provide clear video/image of the sign
3. Include accurate word/phrase mapping
4. Select appropriate language category

### Code Contributions
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Learning Resources

### American Sign Language (ASL)
- Spread the Sign (ASL)
- Handspeak (ASL Dictionary)
- Signing Savvy (ASL Dictionary)
- ASL Pro Dictionary

### Indian Sign Language (ISL)
- Indian Sign Language Dictionary (NISH)
- ISLRTC (Indian Sign Language Research & Training Centre)
- Sign Learn (ISL Video Dictionary)

### Regional Sign Languages
- ISL Dictionary - Indian Sign Language Research
- Indian Sign Language by NIHH (YouTube Channel)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors and sign language experts
- Special thanks to the Vosk project for speech recognition models
- Sign language communities for resources and guidance

## Contact

For questions or suggestions, please open an issue in the repository or contact the maintainers.

---
Created by [MadhavDGS](https://github.com/MadhavDGS)
