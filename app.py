from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import os
import logging
from knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Generate a random secret key
app.secret_key = os.urandom(24)
# Configure session to be more robust
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize knowledge base
kb = KnowledgeBase()
try:
    kb.load_from_file('knowledge_base.json')
except Exception as e:
    logger.error(f"Error loading knowledge base: {str(e)}")

def ensure_session_valid():
    """Ensure the session is valid and contains necessary data"""
    if 'conversation_history' not in session:
        logger.debug("Initializing new conversation history in session")
        session['conversation_history'] = []
    elif not isinstance(session['conversation_history'], list):
        logger.warning("Invalid conversation history format, resetting")
        session['conversation_history'] = []
    return session['conversation_history']

@app.route('/')
def home():
    conversation_history = ensure_session_valid()
    logger.debug(f"Home route accessed. Session contains {len(conversation_history)} messages")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message', '')
        if not message:
            logger.warning("Empty message received")
            return jsonify({'error': 'No message provided'}), 400

        # Get and validate conversation history
        conversation_history = ensure_session_valid()
        logger.debug(f"Processing message: '{message}' with {len(conversation_history)} existing messages")
        
        # Get response from knowledge base
        try:
            response_data = kb.get_response(message, include_similarity=True)
            response = response_data['answer']
            similarity = response_data['similarity']
            
            # Determine context based on similarity
            context = 'high_confidence' if similarity > 0.8 else 'medium_confidence' if similarity > 0.6 else 'low_confidence'
            
            logger.debug(f"Generated response with similarity {similarity:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return jsonify({
                'error': 'Failed to generate response',
                'details': str(e)
            }), 500
        
        # Update conversation history
        try:
            # Add user message
            conversation_history.append({
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'context': context
            })
            
            # Add bot response
            conversation_history.append({
                'bot_response': response,
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'similarity': similarity
            })
            
            # Keep only last 10 messages (5 exchanges)
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
            
            # Update session
            session['conversation_history'] = conversation_history
            session.modified = True
            
            logger.debug(f"Updated conversation history, now contains {len(conversation_history)} messages")
            
        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
            return jsonify({
                'error': 'Failed to update conversation history',
                'details': str(e)
            }), 500

        return jsonify({
            'response': response,
            'context': context,
            'similarity': similarity
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in chat route: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/knowledge', methods=['POST'])
def add_knowledge():
    """Add a new entry to the knowledge base"""
    try:
        data = request.json
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        kb.add_entry(
            question=data['question'],
            answer=data['answer'],
            metadata=data.get('metadata', {})
        )
        
        # Optionally save to file
        kb.save_to_file('knowledge_base.json')
        
        return jsonify({'message': 'Knowledge base entry added successfully'})
        
    except Exception as e:
        logger.error(f"Error adding knowledge base entry: {str(e)}")
        return jsonify({
            'error': 'Failed to add knowledge base entry',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 