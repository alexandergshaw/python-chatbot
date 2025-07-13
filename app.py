# Suppress debug/info logs from noisy libraries and root logger
import logging
logging.basicConfig(level=logging.WARNING)
for noisy_logger in [
    "transformers",
    "sentence_transformers",
    "torch",
    "chatterbot",
    "chatterbot.storage",
    "urllib3"
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)
"""
Main Flask Application for the Chatbot

This file contains the core web application logic for our chatbot. It handles:
1. Web routes for the chat interface
2. Session management for conversation history
3. Integration with the knowledge base
4. Error handling and logging
5. Response generation and confidence scoring
"""

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import os
import logging
from knowledge_base import KnowledgeBase

# Set up logging to help us debug the application
# This will show important information in the console while the app runs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize our Flask web application
app = Flask(__name__)

# Security Configuration
# ---------------------
# Generate a random secret key for session encryption
# This is important for keeping user data secure
app.secret_key = os.urandom(24)

# Session Configuration
# -------------------
# These settings control how user sessions are handled
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data in files
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Sessions expire after 30 minutes
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protect against XSS attacks

# Create and load our knowledge base
# This is where all the chatbot's responses are stored
kb = KnowledgeBase()
try:
    # Try to load existing knowledge from our JSON file
    kb.load_from_file('knowledge_base.json')
except Exception as e:
    # Log any errors that occur during loading
    logger.error(f"Error loading knowledge base: {str(e)}")

def ensure_session_valid():
    """
    Make sure the user's session is properly set up
    
    This function:
    1. Checks if we have a conversation history for this user
    2. Creates a new history if none exists
    3. Validates the format of existing history
    
    Returns:
        list: The conversation history for this user
    """
    if 'conversation_history' not in session:
        # First time user - create new conversation history
        logger.debug("Initializing new conversation history in session")
        session['conversation_history'] = []
    elif not isinstance(session['conversation_history'], list):
        # Something's wrong with the history format - reset it
        logger.warning("Invalid conversation history format, resetting")
        session['conversation_history'] = []
    return session['conversation_history']

@app.route('/')
def home():
    """
    Handle requests to the home page
    
    This function:
    1. Ensures the user has a valid session
    2. Renders the main chat interface
    
    Returns:
        str: The rendered HTML for the home page
    """
    conversation_history = ensure_session_valid()
    logger.debug(f"Home route accessed. Session contains {len(conversation_history)} messages")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle incoming chat messages from users
    
    This function:
    1. Receives the user's message
    2. Gets a response from the knowledge base
    3. Updates the conversation history
    4. Returns the response with confidence information
    
    Returns:
        json: The chatbot's response and metadata
    """
    try:
        # Get the user's message from the request
        message = request.json.get('message', '')
        if not message:
            logger.warning("Empty message received")
            return jsonify({'error': 'No message provided'}), 400

        # Get and validate the user's conversation history
        conversation_history = ensure_session_valid()
        logger.debug(f"Processing message: '{message}' with {len(conversation_history)} existing messages")
        
        # Get response from knowledge base
        try:
            # Ask our knowledge base for the best response
            response_data = kb.get_response(message, include_similarity=True)
            response = response_data['answer']
            similarity = response_data['similarity']
            
            # Determine how confident we are in the response
            # Higher similarity means we found a better match
            context = 'high_confidence' if similarity > 0.8 else \
                     'medium_confidence' if similarity > 0.6 else \
                     'low_confidence'
            
            logger.debug(f"Generated response with similarity {similarity:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Truncate error details to avoid large responses
            err_short = str(e)[:200] + ('...' if len(str(e)) > 200 else '')
            return jsonify({
                'error': 'Failed to generate response',
                'details': err_short
            }), 500
        
        # Update conversation history
        try:
            # Add the user's message to history
            conversation_history.append({
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'context': context
            })
            
            # Add the bot's response to history
            conversation_history.append({
                'bot_response': response,
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'similarity': similarity
            })
            
            # Keep only the last 10 messages (5 exchanges)
            # This prevents the history from growing too large
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
            
            # Save the updated history in the session
            session['conversation_history'] = conversation_history
            session.modified = True  # Tell Flask the session was modified
            
            logger.debug(f"Updated conversation history, now contains {len(conversation_history)} messages")
            
        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
            err_short = str(e)[:200] + ('...' if len(str(e)) > 200 else '')
            return jsonify({
                'error': 'Failed to update conversation history',
                'details': err_short
            }), 500

        # Return the response to the user
        return jsonify({
            'response': response,
            'context': context,
            'similarity': similarity
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in chat route: {str(e)}")
        err_short = str(e)[:200] + ('...' if len(str(e)) > 200 else '')
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': err_short
        }), 500

@app.route('/knowledge', methods=['POST'])
def add_knowledge():
    """
    Add new knowledge to the chatbot's knowledge base
    
    This endpoint allows users to teach the chatbot new responses.
    It expects JSON data with:
    - question: What the user might ask
    - answer: How the chatbot should respond
    - metadata: Optional additional information about this knowledge
    
    Returns:
        json: Success or error message
    """
    try:
        # Get the data from the request
        data = request.json
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Add the new knowledge to our knowledge base
        kb.add_entry(
            question=data['question'],
            answer=data['answer'],
            metadata=data.get('metadata', {})
        )
        
        # Save the updated knowledge base to file
        kb.save_to_file('knowledge_base.json')
        
        return jsonify({'message': 'Knowledge base entry added successfully'})
        
    except Exception as e:
        logger.error(f"Error adding knowledge base entry: {str(e)}")
        err_short = str(e)[:200] + ('...' if len(str(e)) > 200 else '')
        return jsonify({
            'error': 'Failed to add knowledge base entry',
            'details': err_short
        }), 500

if __name__ == '__main__':
    # Start the Flask development server
    # The debug=True setting enables auto-reload when code changes
    app.run(debug=True) 