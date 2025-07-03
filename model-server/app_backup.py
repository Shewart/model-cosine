import numpy as np
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import subprocess
import threading
import time
import speech_recognition as sr
from collections import deque
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

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
camera_active = True
last_spoken = {}

def speak(text):
    now = datetime.now()
    if text.lower() not in last_spoken or (now - last_spoken[text.lower()]) > timedelta(seconds=4):
        try:
            speech_process.stdin.write(text + "\n")
            speech_process.stdin.flush()
            last_spoken[text.lower()] = now
            print(f"🔊 Spoke: {text}")
        except Exception as e:
            print(f"[Speak Error] {e}")

def match_gif(text):
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

def detect_loop():
    global detected_label, camera_active
    
    if not CAMERA_AVAILABLE or cap is None or model is None:
        print("⚠️ Detection loop disabled - camera/model not available")
        return
        
    while True:
        try:
            if not camera_active:
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
                    speech_map = {
                        "iloveyou": "Love you",
                        "thanks": "Thank you",
                        "hello": "Hello how are you?",
                        "yes": "Yes I can",
                        "no": "No I can't",
                        "help": "Help me",
                        "repeat": "Repeat again",
                        "more": "More"
                    }
                    speech = speech_map.get(label.lower(), label)

                    with lock:
                        detected_label = label
                    speak(speech)

            time.sleep(0.1)

        except Exception as e:
            print(f"[Detect Error] {e}")
            time.sleep(1)

def reconnect_camera():
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

def speech_loop():
    global detected_gif
    
    if not CAMERA_AVAILABLE:
        print("⚠️ Speech recognition disabled - dependencies not available")
        return
        
    try:
        r = sr.Recognizer()
        r.energy_threshold = 4000
        r.dynamic_energy_threshold = True

        while True:
            try:
                with sr.Microphone() as source:
                    print("🎤 Listening for speech...")
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.listen(source, timeout=3, phrase_time_limit=5)

                    try:
                        text = r.recognize_google(audio).lower()
                        print(f"🎙️ Recognized: {text}")
                        gif = match_gif(text)

                        with lock:
                            detected_gif = gif

                    except sr.UnknownValueError:
                        print("❓ Could not understand audio")
                    except sr.RequestError as e:
                        print(f"🛑 Speech recognition error: {e}")

            except Exception as e:
                print(f"[Mic Error] {e}")
                time.sleep(1)
    except Exception as e:
        print(f"⚠️ Speech recognition not available: {e}")

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
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

# 🔥 NEW ENDPOINTS FOR AI PARTICIPANT INTEGRATION
@app.route('/api/text-to-sign', methods=['POST'])
def text_to_sign():
    """
    Convert text input to appropriate sign language GIF
    Used by AI participant in video calls
    """
    try:
        data = request.get_json()
        text = data.get('text', '').lower()
        
        # Use existing match_gif function
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
    """
    Get specific sign GIF by name
    """
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
def available_signs():
    """
    Get list of all available sign language animations
    """
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

@app.route('/api/health')
def health_check():
    """
    Health check endpoint for AI participant
    """
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'camera_active': camera_active,
        'server_time': datetime.now().isoformat()
    })

if __name__ == '__main__':
    threading.Thread(target=detect_loop, daemon=True).start()
    threading.Thread(target=speech_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
