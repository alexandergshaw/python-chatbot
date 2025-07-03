from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import random
import re
import json
from collections import deque
import os
import logging

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

# Store last N messages for context
CONTEXT_WINDOW = 5

class ChatBot:
    def __init__(self):
        self.patterns = [
            {
                'patterns': [
                    r'\b(hi|hello|hey|greetings)\b',
                    r'^(hi|hello|hey)\s+there\b', 
                    r'good\s+(morning|afternoon|evening)',
                    r'\bstart\b.*\bconversation\b'
                ],
                'responses': [
                    "Hello! How can I help you today?",
                    "Hi there! What's on your mind?",
                    "Hey! How are you doing?",
                    "Greetings! What brings you here today?",
                    "Hello! I'm here to help. What would you like to discuss?"
                ],
                'context': 'greeting',
                'requires_context': False
            },
            {
                'patterns': [
                    r'how\s+are\s+you',
                    r'how\s+are\s+things',
                    r'how\s+is\s+it\s+going',
                    r'how\s+do\s+you\s+feel',
                    r'what\'s\s+up',
                    r'how\s+have\s+you\s+been'
                ],
                'responses': [
                    "I'm doing well, thanks for asking! How about you?",
                    "I'm great! How can I assist you today?",
                    "All good here! What can I help you with?",
                    "I'm functioning perfectly! What's on your mind?",
                    "I'm having a great day, thanks! How are you doing?"
                ],
                'context': 'well_being',
                'requires_context': False
            },
            {
                'patterns': [
                    r'\b(bye|goodbye|farewell|see\s+you|later)\b',
                    r'have\s+to\s+go',
                    r'got\s+to\s+go',
                    r'leaving\s+now',
                    r'talk\s+to\s+you\s+later'
                ],
                'responses': [
                    "Goodbye! Have a great day!",
                    "See you later! Take care!",
                    "Bye! Come back soon!",
                    "Take care! Looking forward to our next chat!",
                    "Goodbye! It was great talking with you!"
                ],
                'context': 'farewell',
                'requires_context': False
            },
            {
                'patterns': [
                    r'\b(thank\s+you|thanks|appreciate\s+it|grateful)\b',
                    r'that\s+helps?',
                    r'(helpful|useful)\s+information',
                    r'you\'ve?\s+been\s+(helpful|great)'
                ],
                'responses': [
                    "You're welcome! Is there anything else you'd like to know?",
                    "Glad I could help! Let me know if you need anything else.",
                    "Anytime! Feel free to ask more questions.",
                    "Happy to help! What else would you like to explore?",
                    "My pleasure! Is there something else you'd like to discuss?"
                ],
                'context': 'gratitude',
                'requires_context': False
            },
            {
                'patterns': [
                    r'what\s+can\s+you\s+do',
                    r'your\s+capabilities',
                    r'what\s+are\s+you\s+capable\s+of',
                    r'help\s+me\s+with',
                    r'how\s+can\s+you\s+help',
                    r'tell\s+me\s+about\s+yourself'
                ],
                'responses': [
                    "I can help with various tasks! I can answer questions, engage in conversation, remember context, and learn from our interactions. What interests you?",
                    "I'm designed to be helpful! I can maintain context in conversations, provide information, and engage in natural dialogue. What would you like to know?",
                    "I'm a chatbot that can understand context, remember our conversation, and provide helpful responses. I'm particularly good at explaining things and helping you explore topics. What area should we discuss?",
                    "My capabilities include natural conversation, context awareness, and helpful responses. I can also remember our chat history to provide more relevant answers. What would you like to explore?",
                    "I'm here to assist you with information, engage in meaningful conversation, and help you explore various topics. I learn from our interactions to provide better responses. What interests you?"
                ],
                'context': 'capabilities',
                'requires_context': False
            },
            {
                'patterns': [
                    r'tell\s+me\s+(about|more)',
                    r'explain\s+(?:to\s+me)?',
                    r'could\s+you\s+elaborate',
                    r'more\s+details?\s+please',
                    r'what\s+do\s+you\s+mean\s+by\s+that'
                ],
                'responses': [
                    "I'd be happy to explain more. What specific aspect interests you?",
                    "Sure! Could you specify what you'd like to know more about?",
                    "Of course! What details would you like me to focus on?",
                    "I'll be glad to provide more information. Which part would you like me to elaborate on?",
                    "I can explain further. What particular aspect caught your interest?"
                ],
                'context': 'explanation',
                'requires_context': True
            },
            {
                'patterns': [
                    r'why',
                    r'how\s+come',
                    r'what\'s\s+the\s+reason',
                    r'explain\s+why',
                    r'could\s+you\s+explain\s+why'
                ],
                'responses': [
                    "That's an interesting question! Let me explain...",
                    "Good question! Here's what I understand about that...",
                    "Let me share what I know about that...",
                    "There are several factors to consider here...",
                    "That's a thoughtful inquiry. Here's my perspective..."
                ],
                'context': 'reasoning',
                'requires_context': True
            },
            {
                'patterns': [
                    r'i\s+(?:am|feel|\'m)\s+(good|great|fine|okay|happy)',
                    r'doing\s+(?:good|great|fine|okay)',
                    r'all\s+good',
                    r'not\s+bad'
                ],
                'responses': [
                    "I'm glad to hear that! What would you like to discuss?",
                    "That's wonderful! How can I help you today?",
                    "Great to hear! What's on your mind?",
                    "Excellent! What would you like to explore?",
                    "That's good to know! What can I help you with?"
                ],
                'context': 'positive_mood',
                'requires_context': False
            },
            {
                'patterns': [
                    r'i\s+(?:am|feel|\'m)\s+(bad|sad|angry|upset|frustrated)',
                    r'not\s+(?:good|great|okay|fine)',
                    r'having\s+a\s+(?:bad|rough|difficult)\s+(?:day|time)',
                    r'feeling\s+down'
                ],
                'responses': [
                    "I'm sorry to hear that. Would you like to talk about it?",
                    "That must be difficult. Is there something specific you'd like to discuss?",
                    "I understand. Sometimes talking about it can help. What's on your mind?",
                    "I'm here to listen if you want to share more.",
                    "That sounds challenging. How can I help make things better?"
                ],
                'context': 'negative_mood',
                'requires_context': False
            },
            {
                'patterns': [
                    r'that\'s?\s+(?:wrong|incorrect|not\s+right)',
                    r'i\s+disagree',
                    r'not\s+true',
                    r'you\'re\s+mistaken'
                ],
                'responses': [
                    "I apologize for any confusion. Could you help me understand what's incorrect?",
                    "Thank you for pointing that out. Could you explain the correct information?",
                    "I appreciate the feedback. What should I understand differently?",
                    "Let me learn from this. What's the right way to think about it?",
                    "I want to improve my understanding. Could you explain where I went wrong?"
                ],
                'context': 'correction',
                'requires_context': True
            },
            {
                'patterns': [
                    r'you\'re?\s+(?:right|correct)',
                    r'that\'s?\s+(?:right|correct|true)',
                    r'i\s+agree',
                    r'exactly',
                    r'precisely'
                ],
                'responses': [
                    "I'm glad we're on the same page! Would you like to explore this topic further?",
                    "Thank you! Shall we delve deeper into this subject?",
                    "Great that we agree! What aspect would you like to discuss next?",
                    "Excellent! Would you like to know more about any particular aspect?",
                    "I'm happy we understand each other! Where should we take the conversation?"
                ],
                'context': 'agreement',
                'requires_context': True
            },
            {
                'patterns': [
                    r'what\s+do\s+you\s+think\s+about',
                    r'your\s+opinion\s+on',
                    r'what\'s?\s+your\s+take\s+on',
                    r'how\s+do\s+you\s+feel\s+about'
                ],
                'responses': [
                    "That's an interesting topic to explore. While I can provide information and discuss various perspectives, I aim to be objective rather than share personal opinions. What specific aspects would you like to learn about?",
                    "I can help by sharing information and discussing different viewpoints on that topic. What particular aspects interest you?",
                    "While I don't form personal opinions, I can help you explore various perspectives and facts about that topic. What would you like to know?",
                    "I focus on providing helpful information rather than personal views. Would you like to explore the different aspects of this topic?",
                    "Let's explore this topic together! I can share information and discuss various viewpoints. What specific elements interest you?"
                ],
                'context': 'opinion',
                'requires_context': False
            }
        ]
        
        self.context_responses = {
            'greeting': {
                'greeting': [
                    "I already said hello! What can I help you with?",
                    "We've already greeted each other. What's on your mind?",
                    "Hello again! Shall we focus on what brings you here?",
                    "We're already acquainted. What would you like to discuss?",
                    "Since we've said our hellos, what would you like to explore?"
                ],
                'farewell': "Leaving so soon? Well, have a great day!",
                'default': "Now that we've said hello, what would you like to discuss?"
            },
            'well_being': {
                'well_being': [
                    "You seem very concerned about my well-being! I'm still doing great!",
                    "Still doing well! Shall we focus on how I can help you?",
                    "As an AI, I'm consistently operational! What can I do for you?",
                    "Still functioning perfectly! What would you like to discuss?",
                    "I appreciate your concern! I'm still here and ready to help!"
                ],
                'default': "Thanks for asking about me. What's on your mind?"
            },
            'farewell': {
                'greeting': "Oh, are you staying? Hello again!",
                'farewell': [
                    "You've already said goodbye! Take care!",
                    "We've said our goodbyes. Have a wonderful time!",
                    "I understand you're leaving. Take care!",
                    "Goodbye again! Have a great day!",
                    "We've already said farewell. Best wishes!"
                ],
                'default': "Take care! Feel free to come back anytime."
            },
            'explanation': {
                'explanation': [
                    "I notice you'd like more details. Could you be more specific about what interests you?",
                    "I'm happy to explain further. Which aspect would you like me to focus on?",
                    "I can provide more information. What specifically would you like to know?",
                    "Let's explore this in more detail. What particular aspect interests you?",
                    "I can elaborate further. Which part would you like me to explain?"
                ]
            },
            'correction': {
                'correction': [
                    "I see there's still some confusion. Could you explain further?",
                    "Let's work together to get this right. What specifically needs correction?",
                    "I want to ensure accurate information. Could you clarify what needs to be corrected?",
                    "Thank you for your patience. Could you help me understand the issue better?",
                    "I appreciate your help in improving my understanding. What specifically is incorrect?"
                ]
            }
        }

        # Add new response chain patterns
        self.response_chains = {
            'question_answer': {
                'patterns': [
                    r'(?:can|could) you explain (?:more|further|again)',
                    r'(?:why|how) (?:is|does) that',
                    r'what do you mean by that',
                    r'tell me more about (?:that|this)',
                    r'(?:that\'s|is) interesting'
                ],
                'responses': {
                    'explanation': [
                        "Let me elaborate on that. {previous_context}",
                        "I'll explain further. {previous_context}",
                        "To clarify my previous point: {previous_context}",
                        "Here's a more detailed explanation: {previous_context}",
                        "Allow me to expand on that. {previous_context}"
                    ],
                    'general': [
                        "What specific aspect would you like me to explain?",
                        "Which part interests you the most?",
                        "I can provide more details. What would you like to know?",
                        "I'd be happy to elaborate. What aspect interests you?",
                        "There's quite a bit to unpack there. Where should we focus?"
                    ]
                }
            },
            'agreement_chain': {
                'patterns': [
                    r'yes,?\s+(?:that\'s|is) (?:right|correct)',
                    r'exactly!?',
                    r'(?:i|you) (?:got|understand|see) (?:it|that)',
                    r'makes sense',
                    r'i agree'
                ],
                'responses': {
                    'explanation': [
                        "I'm glad that helped! Would you like to explore this topic further?",
                        "Great that we're on the same page! Shall we delve deeper?",
                        "Excellent! What other aspects would you like to discuss?",
                        "Perfect! Would you like to know more about any related topics?",
                        "Wonderful! Where would you like to take the conversation from here?"
                    ]
                }
            },
            'disagreement_chain': {
                'patterns': [
                    r'(?:no|nope),?\s+(?:that\'s|is) (?:not|isn\'t) (?:right|correct|it)',
                    r'i don\'t (?:think|believe) (?:so|that\'s right)',
                    r'(?:you\'re|that\'s) (?:wrong|incorrect)',
                    r'not exactly',
                    r'i disagree'
                ],
                'responses': {
                    'correction': [
                        "I appreciate your correction. Could you help me understand where I went wrong?",
                        "Thank you for the feedback. Could you explain your perspective?",
                        "I see I misunderstood. Could you clarify your point?",
                        "Let's get this right. What's your understanding of it?",
                        "I want to understand better. Could you explain your view?"
                    ]
                }
            },
            'clarification_chain': {
                'patterns': [
                    r'i(?:\'m)? (?:don\'t|do not) (?:understand|get) (?:it|that)',
                    r'(?:what|that\'s) confusing',
                    r'(?:can|could) you (?:say|explain) (?:that|it) (?:again|differently)',
                    r'i\'m lost',
                    r'not sure i follow'
                ],
                'responses': {
                    'explanation': [
                        "Let me try to explain it differently: {previous_context}",
                        "Here's another way to think about it: {previous_context}",
                        "To put it more clearly: {previous_context}",
                        "Let me break it down: {previous_context}",
                        "Perhaps this explanation will help: {previous_context}"
                    ]
                }
            },
            'interest_chain': {
                'patterns': [
                    r'(?:that\'s|sounds|seems) (?:interesting|fascinating|intriguing)',
                    r'tell me more about that',
                    r'i\'d like to know more',
                    r'go on',
                    r'interesting point'
                ],
                'responses': {
                    'exploration': [
                        "I'm glad you find this interesting! What aspect would you like to explore further?",
                        "There's a lot to discuss here. What particularly caught your attention?",
                        "It is fascinating! Would you like to delve into any specific aspect?",
                        "I can share more details. Which part interests you most?",
                        "Let's explore this further. What would you like to know more about?"
                    ]
                }
            },
            'surprise_chain': {
                'patterns': [
                    r'(?:wow|oh|really|seriously)\?',
                    r'i didn\'t know that',
                    r'that\'s surprising',
                    r'interesting!',
                    r'is that so\?'
                ],
                'responses': {
                    'elaboration': [
                        "Yes, indeed! Would you like me to explain more about this?",
                        "It's quite interesting, isn't it? I can share more details if you'd like.",
                        "There's actually even more to it. Would you like to know more?",
                        "It's fascinating! Should we explore this topic further?",
                        "That's just one aspect of it. Would you like to learn more?"
                    ]
                }
            }
        }

    def get_response(self, message, conversation_history):
        # Convert message to lowercase for better matching
        message = message.lower()
        
        # Get current context from conversation history
        current_context = self._get_context(message)
        previous_context = self._get_previous_context(conversation_history)
        
        # Check if this is a response to a previous response
        if len(conversation_history) >= 2:
            chain_response = self._check_response_chains(message, conversation_history)
            if chain_response:
                return chain_response, current_context

        # Check for context-specific responses
        if previous_context and current_context:
            context_response = self._get_context_response(current_context, previous_context)
            if context_response:
                return context_response, current_context

        # Check each pattern for a match
        for pattern_group in self.patterns:
            # Skip patterns that require context if we don't have previous context
            if pattern_group['requires_context'] and not previous_context:
                continue
                
            for pattern in pattern_group['patterns']:
                if re.search(pattern, message):
                    response = random.choice(pattern_group['responses'])
                    
                    # If we have conversation history, try to make response more contextual
                    if conversation_history:
                        response = self._enhance_response_with_context(response, conversation_history)
                    
                    return response, pattern_group['context']

        # If no pattern matches, generate a more sophisticated default response
        return self._generate_default_response(conversation_history), 'general'

    def _get_context(self, message):
        for pattern_group in self.patterns:
            for pattern in pattern_group['patterns']:
                if re.search(pattern, message):
                    return pattern_group['context']
        return 'general'

    def _get_previous_context(self, conversation_history):
        if conversation_history:
            return conversation_history[-1].get('context', 'general')
        return 'general'

    def _get_context_response(self, current_context, previous_context):
        if current_context in self.context_responses:
            context_dict = self.context_responses[current_context]
            if previous_context in context_dict:
                response = context_dict[previous_context]
                if isinstance(response, list):
                    return random.choice(response)
                return response
            return context_dict.get('default')
        return None

    def _check_response_chains(self, message, conversation_history):
        last_bot_response = self._get_last_bot_response(conversation_history)
        last_context = conversation_history[-1].get('context', 'general')
        
        for chain_type, chain_data in self.response_chains.items():
            for pattern in chain_data['patterns']:
                if re.search(pattern, message, re.IGNORECASE):
                    # Get appropriate response set based on context
                    response_set = chain_data['responses'].get(last_context) or chain_data['responses'].get('general')
                    if not response_set:
                        continue
                        
                    # Select and format response
                    response = random.choice(response_set)
                    if '{previous_context}' in response:
                        # Format response with previous context if needed
                        previous_context = self._format_previous_context(last_bot_response)
                        response = response.format(previous_context=previous_context)
                    
                    return response
        
        return None

    def _get_last_bot_response(self, conversation_history):
        # Get the last bot response from history
        for entry in reversed(conversation_history[:-1]):  # Exclude current user message
            if 'bot_response' in entry:
                return entry['bot_response']
        return None

    def _format_previous_context(self, last_response):
        if not last_response:
            return "our previous discussion"
            
        # Remove common prefixes that we add to responses
        prefixes_to_remove = [
            "I'm glad you agree! ",
            "To answer your question: ",
            "I understand your perspective. ",
            "Let me clarify: ",
            "To make it clearer: ",
            "Allow me to explain better: ",
            "To put it another way: ",
            "Here's a clearer explanation: "
        ]
        
        formatted_response = last_response
        for prefix in prefixes_to_remove:
            if formatted_response.startswith(prefix):
                formatted_response = formatted_response[len(prefix):]
                break
        
        return formatted_response

    def _enhance_response_with_context(self, response, conversation_history):
        if len(conversation_history) >= 2:
            last_user_message = conversation_history[-1]['message'].lower()
            last_context = conversation_history[-1].get('context', 'general')
            
            # Enhanced context handling for follow-up responses
            if last_context == 'question' and '?' in last_user_message:
                if any(word in last_user_message for word in ['why', 'how', 'what', 'when', 'where']):
                    response = random.choice([
                        "Let me address that specifically. ",
                        "That's a good question. ",
                        "Here's what I know about that. ",
                        "Let me explain that point. ",
                        "I can help clarify that. "
                    ]) + response
            
            # Enhanced agreement handling
            elif any(word in last_user_message for word in ['yes', 'yeah', 'agree', 'correct', 'right']):
                if last_context == 'explanation':
                    response = random.choice([
                        "I'm glad that explanation helped! ",
                        "Great that you understand! ",
                        "Excellent! Now we can build on that. ",
                        "Perfect! Let's explore further. ",
                        "Wonderful! We can delve deeper if you'd like. "
                    ]) + response
                else:
                    response = random.choice([
                        "I'm glad you agree! ",
                        "Happy we're on the same page! ",
                        "Great that we agree! ",
                        "Excellent point! ",
                        "You're absolutely right! "
                    ]) + response
            
            # Enhanced disagreement handling
            elif any(word in last_user_message for word in ['no', 'nope', 'disagree', 'incorrect', 'wrong']):
                if last_context == 'explanation':
                    response = random.choice([
                        "Let me try to explain it differently. ",
                        "I see where the confusion might be. ",
                        "Thank you for your patience. ",
                        "Let's approach this from another angle. ",
                        "Perhaps I can clarify better. "
                    ]) + response
                else:
                    response = random.choice([
                        "I understand your perspective. ",
                        "Thank you for the correction. ",
                        "I appreciate your viewpoint. ",
                        "You make a good point. ",
                        "Thank you for clarifying. "
                    ]) + response
            
            # Enhanced confusion handling
            elif any(word in last_user_message for word in ['confused', 'don\'t understand', 'what do you mean', 'unclear']):
                if last_context == 'explanation':
                    response = random.choice([
                        "Let me break this down more clearly: ",
                        "Here's a simpler way to explain it: ",
                        "Think of it this way: ",
                        "To make it more straightforward: ",
                        "Let me use a different approach: "
                    ]) + response
                else:
                    response = random.choice([
                        "Let me clarify: ",
                        "To make it clearer: ",
                        "Allow me to explain better: ",
                        "To put it another way: ",
                        "Here's a clearer explanation: "
                    ]) + response

        return response

    def _generate_default_response(self, conversation_history):
        default_responses = [
            "That's interesting! Could you tell me more about that?",
            "I'm curious to hear more about your thoughts on this.",
            "Interesting perspective! How did you come to think about this?",
            "I'm learning from our conversation. Could you elaborate?",
            "That's a unique point! What made you bring this up?",
            "I'd like to understand better. Could you explain further?",
            "That's thought-provoking! What aspects particularly interest you?",
            "I'm intrigued by your comment. What led you to this topic?",
            "Your input is valuable. Could you share more details?",
            "That's worth exploring further. What are your thoughts on this?"
        ]
        
        if conversation_history:
            # Get the last user message (not bot response)
            last_user_message = None
            for entry in reversed(conversation_history):
                if 'message' in entry:  # This is a user message
                    last_user_message = entry['message'].lower()
                    break
            
            if last_user_message:
                # Handle questions
                if '?' in last_user_message:
                    default_responses.extend([
                        "That's a thoughtful question. Let me think about it...",
                        "I'm not entirely sure, but I'm interested in exploring that with you.",
                        "Could you rephrase that? I want to make sure I understand correctly.",
                        "That's an intriguing question. Could you provide more context?",
                        "Let's explore that question together. What are your thoughts?"
                    ])
                
                # Handle statements about thoughts/beliefs
                elif any(word in last_user_message for word in ['think', 'believe', 'feel', 'suppose', 'guess']):
                    default_responses.extend([
                        "Your thoughts on this are valuable. Please tell me more.",
                        "That's a meaningful perspective. What led you to this view?",
                        "I appreciate you sharing your thoughts. Let's explore this further.",
                        "Your insight is interesting. How did you develop this perspective?",
                        "That's a thoughtful observation. Could you elaborate on your reasoning?"
                    ])
                
                # Handle expressions of emotion
                elif any(word in last_user_message for word in ['happy', 'sad', 'angry', 'excited', 'worried', 'concerned']):
                    default_responses.extend([
                        "I understand this is meaningful to you. Would you like to discuss it further?",
                        "Your feelings are valid. Would you like to explore this topic more?",
                        "Thank you for sharing that. What aspects would you like to discuss?",
                        "I appreciate you expressing that. How can I help you with this?",
                        "That's important to acknowledge. How would you like to proceed?"
                    ])

        return random.choice(default_responses)

chatbot = ChatBot()

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
        
        # Get response from chatbot
        try:
            response, context = chatbot.get_response(message, conversation_history)
            logger.debug(f"Generated response: '{response}' with context: {context}")
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return jsonify({
                'error': 'Failed to generate response',
                'details': str(e)
            }), 500
        
        # Update conversation history with both user message and bot response
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
                'context': context
            })
            
            # Keep only last N messages
            if len(conversation_history) > CONTEXT_WINDOW * 2:
                conversation_history = conversation_history[-CONTEXT_WINDOW * 2:]
            
            # Update session
            session['conversation_history'] = conversation_history
            session.modified = True  # Ensure session is saved
            
            logger.debug(f"Updated conversation history, now contains {len(conversation_history)} messages")
            
        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
            return jsonify({
                'error': 'Failed to update conversation history',
                'details': str(e)
            }), 500

        return jsonify({
            'response': response,
            'context': context
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in chat route: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 