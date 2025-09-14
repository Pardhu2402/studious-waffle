from collections import defaultdict

# Initialize spaCy availability
SPACY_AVAILABLE = False
NLP_MODEL = None

# Try to load spaCy and the model
try:
    import spacy
    NLP_MODEL = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
    print("Successfully loaded spaCy and English model")
except ImportError:
    print("Warning: spaCy not available. Using basic text processing.")
except OSError:
    print("Warning: English model not found. Using basic processing.")

class ContextAnalyzer:
    def __init__(self):
        self.context_history = defaultdict(list)
        self.nlp = NLP_MODEL
        
    def analyze(self, text):
        """Enhanced context analysis with grammar structure"""
        context = {
            'subject': None,
            'tense': None,
            'mood': None,
            'topic': None,
            'emotions': [],
            'questions': False,
            'grammar_type': 'statement',  # New: track sentence type
            'non_manual_markers': [],     # New: track facial expressions and body movements
            'emphasis': [],               # New: track emphasized words
            'topicalization': None        # New: track topic-comment structure
        }
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                
                # Enhanced grammar analysis
                self._analyze_grammar_structure(doc, context)
                # Add non-manual markers
                self._add_non_manual_markers(doc, context)
                # Analyze emphasis
                self._analyze_emphasis(doc, context)
                
            except Exception as e:
                print(f"Grammar analysis skipped: {e}")
                self._basic_processing(text, context)
        else:
            self._basic_processing(text, context)
                
        return context
    
    def _analyze_grammar_structure(self, doc, context):
        """Analyze detailed grammar structure"""
        # Detect sentence type
        if any(token.tag_ == "WP" for token in doc):
            context['grammar_type'] = 'question'
            context['non_manual_markers'].append('raised_eyebrows')
        elif any(token.dep_ == "neg" for token in doc):
            context['grammar_type'] = 'negative'
            context['non_manual_markers'].append('head_shake')
        
        # Find subject and topic
        for token in doc:
            if "subj" in token.dep_:
                context['subject'] = token.text
                # Check for topicalization
                if token.i == 0:  # If subject is first
                    context['topicalization'] = token.text
                    context['non_manual_markers'].append('raised_eyebrows')
            
            # Detect tense
            if token.pos_ == "VERB":
                context['tense'] = token.morph.get("Tense", ["present"])[0]
                
    def _add_non_manual_markers(self, doc, context):
        """Add appropriate non-manual markers"""
        # Question markers
        if context['grammar_type'] == 'question':
            if any(token.text.lower() in ['what', 'who', 'where', 'when', 'why', 'how'] for token in doc):
                context['non_manual_markers'].append('furrowed_brows')
                
        # Conditional markers
        if any(token.text.lower() in ['if', 'when', 'suppose'] for token in doc):
            context['non_manual_markers'].append('tilted_head')
            
        # Time markers
        future_words = ['will', 'going', 'future', 'tomorrow', 'later']
        past_words = ['was', 'were', 'had', 'yesterday', 'ago']
        
        if any(token.text.lower() in future_words for token in doc):
            context['non_manual_markers'].append('forward_head_tilt')
        elif any(token.text.lower() in past_words for token in doc):
            context['non_manual_markers'].append('backward_head_tilt')
    
    def _analyze_emphasis(self, doc, context):
        """Analyze word emphasis"""
        for token in doc:
            # Check for uppercase words (emphasis)
            if token.text.isupper() and len(token.text) > 1:
                context['emphasis'].append(token.text)
                context['non_manual_markers'].append('head_nod')
            
            # Check for intensifiers
            if token.text.lower() in ['very', 'really', 'extremely', 'absolutely']:
                context['emphasis'].append(token.nbor().text)  # Emphasize the next word
                context['non_manual_markers'].append('slow_movement')
    
    def _basic_processing(self, text, context):
        """Basic text processing without spaCy"""
        words = text.split()
        
        # Simple question detection
        question_words = ['what', 'who', 'where', 'when', 'why', 'how']
        if any(word.lower() in question_words for word in words):
            context['grammar_type'] = 'question'
            context['non_manual_markers'].append('raised_eyebrows')
        
        # Simple emotion detection
        emotion_words = {
            'happy': ['happy', 'joy', 'glad', 'excited'],
            'sad': ['sad', 'unhappy', 'depressed'],
            'angry': ['angry', 'mad', 'furious'],
            'surprised': ['surprised', 'shocked', 'amazed']
        }
        
        for word in text.lower().split():
            for emotion, indicators in emotion_words.items():
                if word in indicators:
                    context['emotions'].append(emotion)
                    context['non_manual_markers'].append(f'{emotion}_expression')

class GrammarConverter:
    def __init__(self):
        self.nlp = NLP_MODEL
        
    def convert_to_asl(self, text, context):
        """Convert to ASL while preserving original functionality"""
        # Simply return the text for now to maintain current functionality
        return text
        
    def convert_to_isl(self, text, context):
        """Convert to ISL while preserving original functionality"""
        # Simply return the text for now to maintain current functionality
        return text

class ExpressionGenerator:
    def __init__(self):
        self.expression_markers = {
            'raised_eyebrows': 'eyebrows_up',
            'head_shake': 'shake_horizontal',
            'head_nod': 'nod_vertical',
            'tilted_head': 'head_tilt',
            'forward_head_tilt': 'tilt_forward',
            'backward_head_tilt': 'tilt_backward',
            'furrowed_brows': 'eyebrows_down',
            'slow_movement': 'slow_motion',
            'happy_expression': 'smile',
            'sad_expression': 'frown',
            'angry_expression': 'angry_face',
            'surprised_expression': 'wide_eyes'
        }
        
    def add_expressions(self, sign_sequence, context):
        """Add expressions without affecting core translation"""
        return {
            'signs': sign_sequence,
            'expressions': [],  # Empty list to not interfere with current functionality
            'grammar_analysis': context.get('analysis', {}) if context.get('analysis_only') else {}
        } 