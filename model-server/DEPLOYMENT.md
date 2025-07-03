# Deployment Guide for Coolify

## Prerequisites

1. **Coolify Instance**: Make sure you have Coolify installed and running
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)
3. **Docker**: Coolify uses Docker for containerization

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your repository contains these files:
- ✅ `Dockerfile` - Container configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `app.py` - Main application
- ✅ `model/` - ML model files
- ✅ `static/` - Static assets
- ✅ `templates/` - HTML templates

### 2. Connect to Coolify

1. **Login to Coolify** dashboard
2. **Add New Application**
3. **Select Source**: Choose your Git repository
4. **Select Branch**: Usually `main` or `master`

### 3. Configure Build Settings

**Build Configuration:**
- **Build Command**: `docker build -t sign-language-app .`
- **Start Command**: `python app.py`
- **Port**: `5000`

**Environment Variables** (if needed):
```
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### 4. Resource Allocation

**Recommended Resources:**
- **CPU**: 2 cores minimum (4 recommended)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 10GB minimum

### 5. Deploy

1. **Click Deploy** button
2. **Monitor build logs** for any errors
3. **Wait for deployment** to complete
4. **Test the application** at your Coolify URL

## Important Notes

### Camera Access Limitation

⚠️ **Important**: This application requires camera access, which may be limited in containerized environments.

**Solutions:**
1. **Local Development**: Use for testing and development
2. **Cloud Deployment**: Consider using web-based camera APIs
3. **Alternative**: Use pre-recorded videos for demo purposes

### Model Files

Make sure your model files are included in the repository:
- `model/best.pt` (YOLOv8 model)
- `model/cnn_lstm_sign_model.h5` (CNN-LSTM model)

### Performance Optimization

For better performance in production:
1. **Use GPU-enabled containers** if available
2. **Optimize model inference** with TensorRT
3. **Use CDN** for static assets
4. **Enable caching** for better response times

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Check build logs for specific errors

2. **Application Won't Start**
   - Verify start command
   - Check environment variables
   - Review application logs

3. **Camera Not Working**
   - This is expected in containerized environments
   - Consider using web-based alternatives

4. **Memory Issues**
   - Increase RAM allocation
   - Optimize model loading
   - Use model quantization

### Logs and Debugging

- **Build Logs**: Check during deployment
- **Application Logs**: Monitor runtime behavior
- **Docker Logs**: For container-level issues

## Alternative Deployment Options

### 1. Local Docker
```bash
docker build -t sign-language-app .
docker run -p 5000:5000 sign-language-app
```

### 2. Docker Compose
```bash
docker-compose up --build
```

### 3. Cloud Platforms
- **Heroku**: Use Procfile and requirements.txt
- **Railway**: Direct Git deployment
- **Render**: Container deployment
- **DigitalOcean App Platform**: Container-based

## Security Considerations

1. **HTTPS**: Enable SSL/TLS in production
2. **Environment Variables**: Don't commit sensitive data
3. **Input Validation**: Validate all user inputs
4. **Rate Limiting**: Implement API rate limits
5. **CORS**: Configure cross-origin requests properly

## Monitoring

Set up monitoring for:
- **Application Health**: Use health check endpoint
- **Performance Metrics**: Response times, throughput
- **Error Tracking**: Log and monitor errors
- **Resource Usage**: CPU, memory, disk usage

---

**Need Help?** Check the main README.md for more detailed information about the application. 