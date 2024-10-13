from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
from flask_cors import CORS
from dotenv import load_dotenv  # Import dotenv
import os

app = Flask(__name__)
CORS(app)

# Load environment variables from .env file
load_dotenv()

# Fetch the Google Gemini API key from the environment variable
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY is None:
    raise ValueError("API key not set. Please set GEMINI_API_KEY environment variable.")

genai.configure(api_key=API_KEY)

# Function to extract the video ID from a YouTube URL
def extract_video_id(youtube_url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, youtube_url)
    if match:
        return match.group(2)
    else:
        return None

# Function to fetch transcript from YouTube video
def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = ' '.join([t['text'] for t in transcript])
        return full_transcript
    except Exception as e:
        print(f"Error fetching transcript for video {video_id}: {e}")
        return None  # If there's no transcript, return None

# Function to summarize text using Gemini API
def summarize_text_with_gemini(text):
    try:
        # Using the Gemini model to generate a more refined summary
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Updated prompt for better summary quality (focusing on video content)
        prompt = (
            f"Summarize the key points and main message from the content of this video, "
            f"highlighting only the most important takeaways for the viewer. Organize the summary "
            f"into clear sections with headings. Ensure the summary is engaging, concise, and informative. "
            f"Keep the summary between 200 and 300 words, written in a way that makes it easy for someone to "
            f"quickly grasp the core ideas without watching the entire video:\n\n"
            f"{text}\n\n"
            "Structure the summary with sections like:\n"
            "- Introduction (overview of the video's main theme)\n"
            "- Key Insights (highlight important points)\n"
            "- Actionable Advice (practical takeaways)\n"
            "- Conclusion (final thoughts or call to action)"
        )

        response = model.generate_content(prompt)
        
        # Return the generated summary
        return response.text
    except Exception as e:
        print(f"Error summarizing the text with Gemini: {e}")
        return "Error summarizing the text"


# API Endpoint for summarizing a YouTube lecture
@app.route('/summarize', methods=['POST'])
def summarize_video():
    data = request.get_json()
    youtube_url = data.get('youtube_url')

    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400

    # Extract the video ID from the provided URL
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    # Fetch transcript
    transcript = get_transcript(video_id)
    if not transcript:
        return jsonify({'error': 'Transcript not available for this video'}), 404

    # Summarize transcript using Gemini API
    summary = summarize_text_with_gemini(transcript)

    # Return the response as JSON
    return jsonify({'video_id': video_id, 'summary': summary})

if __name__ == '__main__':
    app.run(debug=True)
