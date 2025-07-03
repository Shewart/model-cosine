import numpy as np
from flask import Flask, render_template, Response, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import logging
import time
import re
import subprocess
import threading
from datetime import datetime, timedelta

# Try to import cv2 and YOLO - use fallback if not available
try:
    import cv2
    from ultralytics import YOLO
    CAMERA_AVAILABLE = True
    print("✅ OpenCV and YOLO loaded successfully")
except ImportError as e:
    print(f"⚠️ OpenCV/YOLO not available: {e}")
    print("🔄 Running in GIF-only mode")
    cv2 = None
    YOLO = None
    CAMERA_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Production CORS configuration
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')
CORS(app, origins=cors_origins)

# Configuration
AVATARS_DIR = os.path.join(os.path.dirname(__file__), 'avatars')

# Available sign language words mapping to GIF files
SIGN_MAPPING = {
    'hello': 'hello.gif',
    'hi': 'hello.gif',
    'hey': 'hello.gif',
    'good morning': 'goodmorning.gif',
    'morning': 'goodmorning.gif',
    'how are you': 'howareyou.gif',
    'how': 'howareyou.gif',
    'thanks': 'thanks.gif',
    'thank you': 'thanks.gif',
    'thank': 'thanks.gif',
    'yes': 'yes.gif',
    'okay': 'yes.gif',
    'sure': 'yes.gif',
    'no': 'no.gif',
    'nope': 'no.gif',
    'help': 'helpme.gif',
    'help me': 'helpme.gif',
    'i love you': 'iloveyou.gif',
    'love': 'iloveyou.gif',
    'more': 'more.gif',
    'repeat': 'repeat.gif',
    'again': 'repeat.gif',
    'none': 'none.gif'
}

# Initialize model and speech process only if available
model = None
labels = {}
speech_process = None

if CAMERA_AVAILABLE:
    try:
        model = YOLO("model/best.pt")
        labels = model.names
        print("✅ YOLO model loaded successfully")
    except Exception as e:
        print(f"⚠️ Could not load YOLO model: {e}")
        model = None

    # Initialize speech process
    try:
        speech_process = subprocess.Popen(
            ["sign_lang_env\\Scripts\\python.exe", "speak_worker.py"],
            stdin=subprocess.PIPE,
            text=True
        )
        print("✅ Speech process initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize speech process: {e}")
        speech_process = None

# Camera initialization
def init_camera():
    if not CAMERA_AVAILABLE or cv2 is None:
        print("⚠️ Camera not available - OpenCV not loaded")
        return None
        
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    for backend in backends:
        for index in [0, 1, 2]:
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                print(f"✅ Camera initialized with backend: {backend}, index: {index}")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
            cap.release()
    print("❌ Cannot open webcam. Please check your camera connection.")
    return None

cap = init_camera()

# Global variables
detected_label = "Detecting..."
detected_gif = "none.gif"
lock = threading.Lock()
camera_active = False  # Start with camera inactive
ai_participant_active = False  # Track if AI participant is in meeting
last_spoken = {}
current_sign = 'none'
sign_start_time = time.time()
sign_duration = 4.0

detect_thread = None

def speak(text):
    """Handle text-to-speech with rate limiting"""
    if not speech_process:
        return
        
    now = datetime.now()
    if text.lower() not in last_spoken or (now - last_spoken[text.lower()]) > timedelta(seconds=4):
        try:
            speech_process.stdin.write(text + "\n")
            speech_process.stdin.flush()
            last_spoken[text.lower()] = now
            print(f"🔊 Spoke: {text}")
        except Exception as e:
            print(f"[Speak Error] {e}")

def text_to_sign_mapping(text):
    """Enhanced text to sign mapping with better phrase matching"""
    if not text:
        return 'none.gif'
    
    text = text.lower().strip()
    logger.info(f"🔤 Processing: '{text}'")
    
    # Direct mapping
    if text in SIGN_MAPPING:
        result = SIGN_MAPPING[text]
        logger.info(f"✅ Direct match: {text} -> {result}")
        return result
    
    # Word matches
    words = text.split()
    for word in words:
        if word in SIGN_MAPPING:
            result = SIGN_MAPPING[word]
            logger.info(f"✅ Word match: {word} -> {result}")
            return result
    
    # Semantic matches
    if any(w in text for w in ['hello', 'hi', 'hey']):
        return 'hello.gif'
    elif any(w in text for w in ['how', 'what']):
        return 'howareyou.gif'  
    elif any(w in text for w in ['thank', 'thanks']):
        return 'thanks.gif'
    elif any(w in text for w in ['yes', 'okay', 'sure']):
        return 'yes.gif'
    elif any(w in text for w in ['no', 'nope']):
        return 'no.gif'
    elif any(w in text for w in ['help', 'assist']):
        return 'helpme.gif'
    elif any(w in text for w in ['love', 'care']):
        return 'iloveyou.gif'
    elif any(w in text for w in ['more', 'continue']):
        return 'more.gif'
    elif any(w in text for w in ['repeat', 'again']):
        return 'repeat.gif'
    
    logger.info(f"❌ No match for: '{text}', using none.gif")
    return 'none.gif'

def detect_loop():
    """Camera detection loop that detects signs and triggers speech"""
    global detected_label, camera_active, current_sign, sign_start_time
    
    if not CAMERA_AVAILABLE or cap is None or model is None:
        print("⚠️ Detection loop disabled - camera/model not available")
        return
        
    while True:
        try:
            # Only run detection if AI participant is active
            if not ai_participant_active or not camera_active:
                time.sleep(1)
                continue

            success, frame = cap.read()
            if not success:
                print("⚠️ Frame grab failed, reconnecting...")
                camera_active = False
                reconnect_camera()
                time.sleep(1)
                continue

            results = model.predict(source=frame, stream=False, verbose=False)

            if results and results[0].boxes:
                label_index = int(results[0].boxes.cls[0])
                confidence = float(results[0].boxes.conf[0])

                if confidence > 0.5:
                    label = labels[label_index]
                    
                    # Enhanced speech mapping
                    speech_map = {
                        "iloveyou": "I love you",
                        "thanks": "Thank you",
                        "hello": "Hello, how are you?",
                        "yes": "Yes I can",
                        "no": "No I can't",
                        "help": "Help me",
                        "helpme": "Help me",
                        "repeat": "Please repeat again",
                        "more": "More please",
                        "howareyou": "How are you?",
                        "goodmorning": "Good morning"
                    }
                    speech = speech_map.get(label.lower(), label)

                    with lock:
                        detected_label = label
                        # Update current_sign to drive GIF display
                        current_sign = label.lower()
                        sign_start_time = time.time()
                        print(f"🎭 Detected sign: {label} -> {current_sign}.gif")
                    
                    speak(speech)

            time.sleep(0.1)

        except Exception as e:
            print(f"[Detect Error] {e}")
            time.sleep(1)

def reconnect_camera():
    """Reconnect camera if connection is lost"""
    global cap, camera_active
    if not CAMERA_AVAILABLE:
        return
        
    try:
        if cap:
            cap.release()
        cap = init_camera()
        camera_active = cap is not None
        if camera_active:
            print("✅ Camera reconnected")
        else:
            print("❌ Camera reconnection failed")
    except Exception as e:
        print(f"❌ Camera reconnection failed: {e}")
        camera_active = False

def start_detection_thread():
    global detect_thread, camera_active
    if detect_thread is None or not detect_thread.is_alive():
        camera_active = True
        detect_thread = threading.Thread(target=detect_loop, daemon=True)
        detect_thread.start()
        logger.info("🤖 AI Participant activated - Camera detection started")
    else:
        logger.info("🤖 Detection thread already running")

def stop_detection_thread():
    global camera_active
    camera_active = False
    logger.info("🤖 AI Participant deactivated - Camera detection stopped")

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        gifs = [f for f in os.listdir(AVATARS_DIR) if f.endswith('.gif')]
        return jsonify({
            'status': 'healthy',
            'message': 'Enhanced Flask server with speech running',
            'available_gifs': len(gifs),
            'gifs': gifs,
            'current_sign': current_sign,
            'model_loaded': model is not None,
            'camera_active': camera_active,
            'speech_available': speech_process is not None,
            'server_time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get-sign-gif/<sign_name>', methods=['GET'])
def get_sign_gif(sign_name):
    try:
        # Map sign names to available GIFs
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
        
        gif_filename = available_gifs.get(sign_name.lower(), 'none.gif')
        
        logger.info(f"🎬 Serving: {gif_filename}")
        return send_from_directory(AVATARS_DIR, gif_filename, mimetype='image/gif')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/text-to-sign', methods=['POST'])
def text_to_sign():
    global current_sign, sign_start_time
    
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        logger.info(f"🎯 TEXT-TO-SIGN: '{text}'")
        
        gif_filename = text_to_sign_mapping(text)
        sign_name = gif_filename.replace('.gif', '')
        
        current_sign = sign_name
        sign_start_time = time.time()
        
        response = {
            'success': True,
            'text': text,
            'sign': sign_name,
            'gif': gif_filename,
            'gif_filename': gif_filename,
            'gif_url': f'/api/get-sign-gif/{sign_name}',
            'timestamp': time.time()
        }
        
        logger.info(f"📤 RESPONSE: {response}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/current-sign', methods=['GET'])
def get_current_sign():
    return jsonify({
        'sign': current_sign,
        'gif_filename': f'{current_sign}.gif',
        'gif_url': f'/api/get-sign-gif/{current_sign}'
    })

@app.route('/api/ai-participant/activate', methods=['POST'])
def activate_ai_participant():
    global ai_participant_active
    try:
        ai_participant_active = True
        start_detection_thread()
        return jsonify({
            'success': True,
            'message': 'AI participant activated',
            'ai_participant_active': ai_participant_active,
            'camera_active': camera_active
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-participant/deactivate', methods=['POST'])
def deactivate_ai_participant():
    global ai_participant_active, current_sign
    try:
        ai_participant_active = False
        stop_detection_thread()
        current_sign = 'none'  # Reset to none when deactivated
        return jsonify({
            'success': True,
            'message': 'AI participant deactivated',
            'ai_participant_active': ai_participant_active,
            'camera_active': camera_active
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-participant/status', methods=['GET'])
def get_ai_participant_status():
    """Get current AI participant and camera status"""
    return jsonify({
        'ai_participant_active': ai_participant_active,
        'camera_active': camera_active,
        'current_sign': current_sign,
        'camera_available': CAMERA_AVAILABLE,
        'model_loaded': model is not None
    })

@app.route('/api/available-signs')
def available_signs():
    """Get list of all available sign language animations"""
    signs = [
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
    
    return jsonify({
        'success': True,
        'signs': signs,
        'total': len(signs)
    })

# Routes for the web interface (from backup)
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except:
        return jsonify({
            'message': 'Co-Sign Enhanced Server with Speech',
            'version': '2.0.0',
            'status': 'ready',
            'current_sign': current_sign,
            'speech_available': speech_process is not None
        })

def gen_frames():
    """Generate camera frames for web interface"""
    while True:
        try:
            if not CAMERA_AVAILABLE or cv2 is None or cap is None:
                # Create a simple placeholder frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # Add text without cv2 - just return a simple static frame
                import io
                from PIL import Image
                
                # Create simple image with PIL instead of OpenCV
                img = Image.new('RGB', (640, 480), color='black')
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG')
                frame_bytes = buffer.getvalue()
                
            elif not camera_active:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera Disconnected", (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                frame = cv2.resize(frame, (640, 480))
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
            else:
                success, frame = cap.read()
                if not success:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "Frame Error", (50, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            frame = cv2.resize(frame, (640, 480))
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
                
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"[Frame Error] {e}")
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get-status')
def get_status():
    with lock:
        return jsonify({
            'label': detected_label,
            'gif': detected_gif,
            'camera_status': 'active' if camera_active else 'inactive'
        })

if __name__ == '__main__':
    # Do NOT start detection thread at startup
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    logger.info(f"🚀 Starting Enhanced Co-Sign Server with Speech on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
