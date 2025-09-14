from language_processor import ContextAnalyzer, GrammarConverter, ExpressionGenerator
import json
import os
import datetime

class SignTranslator:
    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.grammar_converter = GrammarConverter()
        self.expression_generator = ExpressionGenerator()
        self.feedback_data = []
        self.feedback_dir = os.path.join(os.path.dirname(__file__), 'feedback')
        self.feedback_file = os.path.join(self.feedback_dir, 'feedback_data.json')
        
        # Create feedback directory if it doesn't exist
        if not os.path.exists(self.feedback_dir):
            os.makedirs(self.feedback_dir)
            
        # Load existing feedback
        self._load_feedback()
        
    def translate(self, text, target_language='asl'):
        """Translate text to sign language with context awareness"""
        # Analyze context
        context = self.context_analyzer.analyze(text)
        
        # Convert grammar based on target language
        if target_language == 'isl':
            sign_sequence = self.grammar_converter.convert_to_isl(text, context)
        else:
            sign_sequence = self.grammar_converter.convert_to_asl(text, context)
            
        # Add expressions
        final_sequence = self.expression_generator.add_expressions(sign_sequence, context)
        final_sequence['context'] = context  # Include context in response
        
        return final_sequence
        
    def learn_from_feedback(self, original, correction):
        """Learn from user feedback"""
        feedback_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'original': original,
            'correction': correction,
            'context': self.context_analyzer.analyze(original),
            'processed': False  # Flag for processing feedback later
        }
        self.feedback_data.append(feedback_entry)
        
        # Save feedback data
        self._save_feedback()
        
        # Log feedback for review
        self._log_feedback(feedback_entry)
        
        return True
        
    def _save_feedback(self):
        """Save feedback data to JSON file"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, ensure_ascii=False)
            print(f"Feedback saved to {self.feedback_file}")
        except Exception as e:
            print(f"Error saving feedback: {e}")
            
    def _load_feedback(self):
        """Load previous feedback data"""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_data = json.load(f)
                print(f"Loaded {len(self.feedback_data)} feedback entries")
        except Exception as e:
            print(f"Error loading feedback: {e}")
            self.feedback_data = []
            
    def _log_feedback(self, entry):
        """Log feedback to a separate log file"""
        log_file = os.path.join(self.feedback_dir, 'feedback.log')
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Feedback Entry {entry['timestamp']} ---\n")
                f.write(f"Original: {entry['original']}\n")
                f.write(f"Correction: {entry['correction']}\n")
                f.write(f"Context: {entry['context']}\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            print(f"Error logging feedback: {e}")
            
    def get_feedback_stats(self):
        """Get statistics about collected feedback"""
        return {
            'total_entries': len(self.feedback_data),
            'processed_entries': sum(1 for entry in self.feedback_data if entry['processed']),
            'unprocessed_entries': sum(1 for entry in self.feedback_data if not entry['processed']),
            'latest_feedback': self.feedback_data[-1] if self.feedback_data else None
        } 