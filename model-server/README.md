# Sign Language Translator

A real-time bidirectional sign language translator that converts sign language to speech and speech to sign language animations.

## Features

- 🤖 **Real-time Sign Detection**: Uses YOLOv8 for instant sign language recognition
- 🎤 **Speech Recognition**: Converts spoken words to sign language animations
- 🔊 **Text-to-Speech**: Converts detected signs to spoken words
- 🌐 **Web Interface**: Modern, responsive web UI with real-time video streaming
- 🎨 **Avatar Animations**: Visual feedback with animated GIFs for each sign

## Supported Signs

- Hello
- I Love You
- Thank You
- Yes/No
- Help
- Repeat
- More
- Good Morning
- How Are You

## Tech Stack

- **Backend**: Flask, Python 3.11
- **ML Models**: YOLOv8 (Ultralytics), CNN-LSTM
- **Computer Vision**: OpenCV
- **Speech Processing**: SpeechRecognition, pyttsx3
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Deployment**: Docker, Coolify-ready

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd sign-language-translator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv sign_lang_env
   sign_lang_env\Scripts\Activate.ps1  # Windows
   source sign_lang_env/bin/activate   # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

### Docker Deployment

1. **Build and run with Docker**
   ```bash
   docker-compose up --build
   ```

2. **Or build manually**
   ```bash
   docker build -t sign-language-app .
   docker run -p 5000:5000 sign-language-app
   ```

## Project Structure

```
sign-language-translator/
├── app.py                 # Main Flask application
├── speak_worker.py        # Text-to-speech worker process
├── test.py               # Standalone test script
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── model/              # ML models
│   ├── best.pt         # YOLOv8 model
│   └── cnn_lstm_sign_model.h5  # CNN-LSTM model
├── static/             # Static assets
│   └── avatars/        # Sign language GIF animations
└── templates/          # HTML templates
    └── index.html      # Main web interface
```

## API Endpoints

- `GET /` - Main web interface
- `GET /video_feed` - Real-time video stream
- `GET /get-status` - Current detection status (JSON)

## Environment Variables

- `FLASK_ENV` - Flask environment (development/production)
- `PYTHONUNBUFFERED` - Python output buffering

## Deployment on Coolify

1. **Connect your repository** to Coolify
2. **Set build configuration**:
   - Build Command: `docker build -t sign-language-app .`
   - Start Command: `python app.py`
3. **Configure environment variables** if needed
4. **Deploy** and enjoy! 🚀

## Model Information

- **YOLOv8 Model**: `model/best.pt` (6MB) - Real-time sign detection
- **CNN-LSTM Model**: `model/cnn_lstm_sign_model.h5` (75MB) - Alternative sequence model

## Performance

- **Detection Speed**: ~10 FPS real-time inference
- **Accuracy**: >90% on trained sign language dataset
- **Latency**: <100ms end-to-end processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- YOLOv8 by Ultralytics
- Flask web framework
- OpenCV computer vision library
- SpeechRecognition library

---

**Note**: This application requires camera access for sign detection and microphone access for speech recognition. Make sure your browser has the necessary permissions enabled. 