import os
from flask import Flask, render_template, request, jsonify, session
from bot_logic import manage_dialogue
import requests
import time
import json
from helpers.logger import Logger


# Global singleton instance
logger = Logger().get_logger()

# Initialize Flask App
app = Flask(__name__)
# A secret key is required for Flask sessions
app.secret_key = os.urandom(24)


def call_gemini_api(prompt):
    """
    Calls the Gemini API with exponential backoff.
    """
    # As per instructions, apiKey is an empty string and the model is gemini-2.5-flash-preview-09-2025
    apiKey = ""
    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={apiKey}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    max_retries = 5
    delay = 1  # start with 1 second

    for attempt in range(max_retries):
        try:
            response = requests.post(apiUrl, headers=headers, data=json.dumps(payload), timeout=20)

            if response.status_code == 200:
                result = response.json()
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text:
                    return text
                else:
                    return "Sorry, I couldn't generate a response. The API returned empty content."

            # Do not retry on client errors (4xx)
            if 400 <= response.status_code < 500:
                return f"Sorry, there was an error with the request ({response.status_code})."

            # Retry on server errors (5xx)
            logger.info(f"Server error ({response.status_code}). Retrying in {delay}s...")

        except requests.exceptions.RequestException as e:
            logger.info(f"Request failed ({e}). Retrying in {delay}s...")

        time.sleep(delay)
        delay *= 2  # Exponential backoff

    return "Sorry, I'm having trouble connecting to the generative AI service right now. Please try again later."


@app.route('/')
def index():
    """
    Serves the main HTML page for the chat interface.
    """
    # Clear any previous session data on load
    session.clear()
    session['user_id'] = 'user_' + os.urandom(8).hex()
    session['context'] = {}
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles the POST request from the chat interface.
    Processes message, checks for Gemini actions, and returns response.
    """
    try:
        # Get message from the request
        message = request.json['message']

        # Ensure session context exists
        if 'context' not in session:
            session['context'] = {}
        if 'user_id' not in session:
            session['user_id'] = 'user_' + os.urandom(8).hex()

        # Get user ID from session
        user_id = session.get('user_id')

        # 1. Process the message using the dialogue manager
        bot_response, new_context = manage_dialogue(user_id, session['context'], message)

        # 2. Check if the dialogue manager queued a Gemini action
        gemini_prompt = new_context.pop('gemini_prompt', None)
        final_response = bot_response

        if gemini_prompt:
            # 3. Call Gemini API if a prompt exists
            logger.info(f"Calling Gemini with prompt: {gemini_prompt}")
            gemini_text = call_gemini_api(gemini_prompt)
            # 4. Append Gemini response to the bot's response
            final_response = f"{bot_response}\n\n{gemini_text}"

        # Update the session context
        session['context'] = new_context
        # We must manually save the session if it's modified
        session.modified = True

        return jsonify({'response': final_response})

    except Exception as e:
        logger.info(f"Error in /chat endpoint: {e}")
        return jsonify({'response': 'Sorry, I encountered an internal error. Please try again.'}), 500


if __name__ == '__main__':
    """
    Runs the Flask application in debug mode.
    """
    app.run(host='0.0.0.0', port=5001, debug=True)
