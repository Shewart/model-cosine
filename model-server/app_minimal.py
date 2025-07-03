"""
Minimal Flask Model Server for AI Participant Integration
This version serves GIFs without camera/cv2 dependencies for testing
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for sign detection simulation
detected_label = "hello"
detected_gif = "hello.gif"
current_sign_index = 0

# Available signs (matching your GIF files)
available_signs = [
    {'name': 'hello', 'display': 'Hello', 'gif': 'hello.gif'},
    {'name': 'thanks', 'display': 'Thank You', 'gif': 'thanks.gif'},
    {'name': 'yes', 'display': 'Yes', 'gif': 'yes.gif'},
    {'name': 'no', 'display': 'No', 'gif': 'no.gif'},
    {'name': 'help', 'display': 'Help Me', 'gif': 'helpme.gif'},
    {'name': 'repeat', 'display': 'Repeat', 'gif': 'repeat.gif'},
    {'name': 'more', 'display': 'More', 'gif': 'more.gif'},
    {'name': 'iloveyou', 'display': 'I Love You', 'gif': 'iloveyou.gif'},
    {'name': 'howareyou', 'display': 'How Are You', 'gif': 'howareyou.gif'},
    {'name': 'goodmorning', 'display': 'Good Morning', 'gif': 'goodmorning.gif'}
]

def match_gif(text):
    """Map text to appropriate GIF file"""
    phrase_map = {
        "hello": "hello.gif",
        "how are you": "howareyou.gif",
        "i am fine": "iamfine.gif",
        "love you": "iloveyou.gif",
        "thank you": "thanks.gif",
        "yes": "yes.gif",
        "no": "no.gif",
        "repeat": "repeat.gif",
        "more": "more.gif",
        "help me": "helpme.gif",
        "good morning": "goodmorning.gif"
    }
    text = text.lower()
    for phrase in phrase_map:
        if phrase in text:
            return phrase_map[phrase]
    return "none.gif"

def cycle_signs():
    """Cycle through signs for demonstration"""
    global detected_label, detected_gif, current_sign_index
    
    while True:
        try:
            current_sign = available_signs[current_sign_index]
            detected_label = current_sign['name']
            detected_gif = current_sign['gif']
            
            print(f"🔄 Cycling to: {current_sign['display']} ({current_sign['gif']})")
            
            current_sign_index = (current_sign_index + 1) % len(available_signs)
            time.sleep(5)  # Change sign every 5 seconds
            
        except Exception as e:
            print(f"[Cycle Error] {e}")
            time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-status')
def get_status():
    return jsonify({
        'label': detected_label,
        'gif': detected_gif,
        'camera_status': 'simulated'  # No real camera in minimal version
    })

# API ENDPOINTS FOR AI PARTICIPANT INTEGRATION
@app.route('/api/text-to-sign', methods=['POST'])
def text_to_sign():
    """Convert text input to appropriate sign language GIF"""
    try:
        data = request.get_json()
        text = data.get('text', '').lower()
        
        gif_name = match_gif(text)
        
        return jsonify({
            'success': True,
            'gif': gif_name,
            'text': text,
            'gif_url': f'/static/avatars/{gif_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-sign-gif/<sign_name>')
def get_sign_gif(sign_name):
    """Get specific sign GIF by name"""
    try:
        available_gifs = {
            'hello': 'hello.gif',
            'thanks': 'thanks.gif', 
            'thank_you': 'thanks.gif',
            'yes': 'yes.gif',
            'no': 'no.gif',
            'help': 'helpme.gif',
            'help_me': 'helpme.gif',
            'repeat': 'repeat.gif',
            'more': 'more.gif',
            'i_love_you': 'iloveyou.gif',
            'iloveyou': 'iloveyou.gif',
            'how_are_you': 'howareyou.gif',
            'howareyou': 'howareyou.gif',
            'good_morning': 'goodmorning.gif',
            'goodmorning': 'goodmorning.gif',
            'none': 'none.gif'
        }
        
        gif_file = available_gifs.get(sign_name.lower(), 'none.gif')
        
        return jsonify({
            'success': True,
            'gif': gif_file,
            'gif_url': f'/static/avatars/{gif_file}',
            'sign': sign_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/available-signs')
def get_available_signs():
    """Get list of all available sign language animations"""
    return jsonify({
        'success': True,
        'signs': available_signs,
        'total': len(available_signs)
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint for AI participant"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': True,  # Simulated
        'camera_active': False,  # No camera in minimal version
        'server_time': datetime.now().isoformat(),
        'version': 'minimal'
    })

if __name__ == '__main__':
    print("🚀 Starting Minimal Flask Model Server...")
    print("📝 Available signs:", [sign['name'] for sign in available_signs])
    print("🔄 Starting sign cycling...")
    
    # Start sign cycling in background
    threading.Thread(target=cycle_signs, daemon=True).start()
    
    print("✅ Server ready!")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 