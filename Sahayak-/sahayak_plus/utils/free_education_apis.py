import requests
import json
import urllib.parse
from typing import Dict, List, Optional

class FreeEducationAPIs:
    """Integration with free education APIs for Sahayak+"""
    
    def __init__(self):
        self.openlibrary_base = "https://openlibrary.org"
        self.nasa_base = "https://images-api.nasa.gov"
        self.wikipedia_base = "https://en.wikipedia.org/api/rest_v1"
        self.opentrivia_base = "https://opentdb.com/api.php"
    
    def search_openlibrary_books(self, query: str, limit: int = 10) -> Dict:
        """Search books using Open Library API"""
        try:
            # Encode query for URL
            encoded_query = urllib.parse.quote(query)
            url = f"{self.openlibrary_base}/search.json?q={encoded_query}&limit={limit}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process and format results
            books = []
            for book in data.get('docs', []):
                book_info = {
                    'title': book.get('title', 'Unknown Title'),
                    'author': book.get('author_name', ['Unknown Author'])[0] if book.get('author_name') else 'Unknown Author',
                    'year': book.get('first_publish_year', 'Unknown Year'),
                    'key': book.get('key', ''),
                    'cover_id': book.get('cover_i'),
                    'ebook_access': book.get('ebook_access', 'no_ebook'),
                    'has_fulltext': book.get('has_fulltext', False),
                    'language': book.get('language', ['eng'])[0] if book.get('language') else 'eng',
                    'url': f"https://openlibrary.org{book.get('key', '')}" if book.get('key') else None
                }
                books.append(book_info)
            
            return {
                'success': True,
                'total_found': data.get('numFound', 0),
                'books': books
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error searching books: {str(e)}'
            }
    
    def search_nasa_images(self, query: str, limit: int = 10) -> Dict:
        """Search images and videos using NASA API"""
        try:
            params = {
                'q': query,
                'media_type': 'image,video'
            }
            response = requests.get(f"{self.nasa_base}/search", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = []
            for item in data.get('collection', {}).get('items', [])[:limit]:
                data0 = item.get('data', [{}])[0]
                media_type = data0.get('media_type', 'image')
                nasa_id = data0.get('nasa_id', '')
                href = item.get('href', '')
                links = item.get('links', [])
                image_url = None
                video_url = None
                original_url = None
                # Extract image_url for images
                if media_type == 'image' and href:
                    try:
                        asset_resp = requests.get(href, timeout=5)
                        asset_resp.raise_for_status()
                        asset_list = asset_resp.json() if asset_resp.headers.get('Content-Type','').startswith('application/json') else asset_resp.text.split('\n')
                        if isinstance(asset_list, list) and asset_list:
                            # Use the first jpg/png
                            for url in asset_list:
                                if url.lower().endswith(('.jpg','.jpeg','.png')):
                                    image_url = url
                                    break
                            if not image_url:
                                image_url = asset_list[0]
                    except Exception:
                        image_url = None
                # Extract video_url for videos
                if media_type == 'video' and links:
                    for l in links:
                        if l.get('render') == 'mp4' and l.get('href','').endswith('.mp4'):
                            video_url = l['href']
                            break
                        if 'youtube.com' in l.get('href','') or 'youtu.be' in l.get('href',''):
                            video_url = l['href']
                            break
                # Fallback: try to get video_url from asset manifest
                if media_type == 'video' and not video_url and href:
                    try:
                        asset_resp = requests.get(href, timeout=5)
                        asset_resp.raise_for_status()
                        asset_list = asset_resp.json() if asset_resp.headers.get('Content-Type','').startswith('application/json') else asset_resp.text.split('\n')
                        if isinstance(asset_list, list):
                            for url in asset_list:
                                if url.lower().endswith('.mp4'):
                                    video_url = url
                                    break
                    except Exception:
                        video_url = None
                # Try to get original_url from links
                for l in links:
                    if l.get('rel') == 'preview' and l.get('href'):
                        original_url = l['href']
                        break
                # Fallback: use NASA public page
                if not original_url and nasa_id:
                    from urllib.parse import quote
                    original_url = f"https://images.nasa.gov/details/{quote(nasa_id)}"
                item_info = {
                    'title': data0.get('title', 'Untitled'),
                    'description': data0.get('description', 'No description available'),
                    'date_created': data0.get('date_created', 'Unknown Date'),
                    'media_type': media_type,
                    'nasa_id': nasa_id,
                    'keywords': data0.get('keywords', []),
                    'href': href,
                    'links': links,
                    'image_url': image_url,
                    'video_url': video_url,
                    'original_url': original_url
                }
                items.append(item_info)
            return {
                'success': True,
                'total_found': len(data.get('collection', {}).get('items', [])),
                'items': items
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error searching NASA images: {str(e)}'
            }
    
    def get_wikipedia_summary(self, topic: str) -> Dict:
        """Get topic summary from Wikipedia API"""
        try:
            # Encode topic for URL
            encoded_topic = urllib.parse.quote(topic)
            url = f"{self.wikipedia_base}/page/summary/{encoded_topic}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            summary_info = {
                'title': data.get('title', topic),
                'extract': data.get('extract', 'No summary available'),
                'content_url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'thumbnail': data.get('thumbnail', {}).get('source', '') if data.get('thumbnail') else None,
                'page_id': data.get('pageid'),
                'language': data.get('lang', 'en')
            }
            
            return {
                'success': True,
                'summary': summary_info
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting Wikipedia summary: {str(e)}'
            }
    
    def get_opentrivia_quiz(self, category: int = 9, difficulty: str = 'easy', 
                           amount: int = 5, question_type: str = 'multiple') -> Dict:
        """Get quiz questions from Open Trivia DB"""
        try:
            params = {
                'amount': amount,
                'category': category,
                'difficulty': difficulty,
                'type': question_type
            }
            
            response = requests.get(self.opentrivia_base, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('response_code') != 0:
                return {
                    'success': False,
                    'error': f'API error: {data.get("response_code")}'
                }
            
            # Process and format results
            questions = []
            for q in data.get('results', []):
                question_info = {
                    'question': q.get('question', ''),
                    'correct_answer': q.get('correct_answer', ''),
                    'incorrect_answers': q.get('incorrect_answers', []),
                    'category': q.get('category', ''),
                    'difficulty': q.get('difficulty', ''),
                    'type': q.get('type', ''),
                    'all_answers': [q.get('correct_answer', '')] + q.get('incorrect_answers', [])
                }
                questions.append(question_info)
            
            return {
                'success': True,
                'total_questions': len(questions),
                'questions': questions
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting quiz: {str(e)}'
            }
    
    def get_opentrivia_categories(self) -> Dict:
        """Get available categories from Open Trivia DB"""
        try:
            url = "https://opentdb.com/api_category.php"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            categories = []
            for cat in data.get('trivia_categories', []):
                category_info = {
                    'id': cat.get('id'),
                    'name': cat.get('name')
                }
                categories.append(category_info)
            
            return {
                'success': True,
                'categories': categories
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting categories: {str(e)}'
            }
    
    def generate_quiz_from_wikipedia(self, topic: str, num_questions: int = 5) -> Dict:
        """Generate quiz questions from Wikipedia summary using AI prompts"""
        try:
            # Get Wikipedia summary first
            wiki_result = self.get_wikipedia_summary(topic)
            
            if not wiki_result['success']:
                return wiki_result
            
            summary = wiki_result['summary']['extract']
            
            # Create AI prompt for quiz generation
            prompt = f"""
            Based on the following information about {topic}, create {num_questions} multiple choice questions.
            
            Information:
            {summary}
            
            Please create questions in this format:
            1. Question: [question text]
               A) [option A]
               B) [option B]
               C) [option C]
               D) [option D]
               Correct Answer: [letter]
            
            Make sure the questions are educational and appropriate for students.
            """
            
            # This would typically use your Gemini API
            # For now, return the summary with a note about AI generation
            return {
                'success': True,
                'topic': topic,
                'summary': summary,
                'ai_prompt': prompt,
                'note': 'Use this prompt with your Gemini API to generate quiz questions'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating quiz: {str(e)}'
            }

# Create a global instance
free_apis = FreeEducationAPIs() 