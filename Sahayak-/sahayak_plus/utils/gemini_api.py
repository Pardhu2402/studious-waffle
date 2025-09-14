import os
import google.generativeai as genai
from PIL import Image

# Configure the Gemini API
genai.configure(api_key="AIzaSyBnjwhSlEWoLAzUEmZwC3HeAcLJRNAk9i4")

def gemini_text(prompt):
    """Generate text response using Gemini Flash"""
    try:
        # Use Gemini 2.0 Flash model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: Could not get response from Gemini. {str(e)}"

def gemini_multimodal(image_path, grade):
    """Generate worksheet from image using Gemini Flash"""
    try:
        # Use Gemini 2.0 Flash model for both text and images
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Load and process the image
        image = Image.open(image_path)
        
        # Create a prompt for worksheet generation
        prompt = f"""
        Analyze this textbook image and create an age-appropriate worksheet for {grade} students.
        
        Please include:
        1. 5-10 comprehension questions based on the content
        2. 2-3 creative activities related to the topic
        3. Vocabulary words with definitions (if applicable)
        4. A short writing prompt
        
        Format the worksheet clearly with sections and make it engaging for students.
        """
        
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"Error generating worksheet: {str(e)}"

def gemini_weekly_lesson_plan(topic, grade, objectives, language):
    """Generate a week-long lesson plan using Gemini Flash"""
    try:
        prompt = f"""
        Create a detailed week-long lesson plan for the topic: '{topic}' for grade: '{grade}' students.
        The learning objectives are: {objectives}.
        The plan should be in {language}.
        Structure the plan as follows:
        - Start with a short summary/overview.
        - For each day (Monday to Friday), output the first line as 'Day: Main Topic' (e.g., 'Monday: Introduction to Photosynthesis and Plant Cell Structures').
        - On the following lines, provide details for that day: objectives, activities, discussions, and assessments, each as bullet points or short paragraphs.
        - Use clear, concise language and include activities, discussions, and assessments where appropriate.
        - Format the output so each day's section starts with the day name and main topic on the first line, followed by the details on the next lines.
        """
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: Could not generate lesson plan. {str(e)}"
