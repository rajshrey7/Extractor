# Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- Tesseract OCR

### Quick Start

1. **Clone and setup**:
```bash
git clone https://github.com/rajshrey7/Extractor.git
cd Extractor
git checkout feat/mosip-integration
```

2. **Backend setup**:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start backend
python main.py
```

3. **Frontend setup**:
```bash
cd frontend
npm install
npm start
```

4. **Mock MOSIP server**:
```bash
cd mock_mosip
python mock_mosip_server.py
```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Backend API: http://localhost:9000
- Frontend: http://localhost:3000
- Mock MOSIP: http://localhost:7000

## Production Deployment

### Render Deployment

1. **Backend on Render**:
- Create new Web Service
- Connect GitHub repository
- Set branch to `feat/mosip-integration`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`
- Add environment variables from `.env.example`

2. **Frontend on Render**:
- Create new Static Site
- Connect GitHub repository
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `frontend/build`
- Add environment variable: `REACT_APP_API_URL=https://your-backend.onrender.com`

### Google Cloud Platform (GCP)

1. **Setup Cloud Run**:
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/extractor-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/extractor-frontend ./frontend

# Deploy services
gcloud run deploy extractor-backend \
  --image gcr.io/PROJECT_ID/extractor-backend \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "MOSIP_MODE=live"

gcloud run deploy extractor-frontend \
  --image gcr.io/PROJECT_ID/extractor-frontend \
  --platform managed \
  --allow-unauthenticated
```

### AWS Deployment

1. **Using ECS**:
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT].dkr.ecr.us-east-1.amazonaws.com

docker build -t extractor-backend .
docker tag extractor-backend:latest [ACCOUNT].dkr.ecr.us-east-1.amazonaws.com/extractor-backend:latest
docker push [ACCOUNT].dkr.ecr.us-east-1.amazonaws.com/extractor-backend:latest

# Create ECS task definition and service
aws ecs create-service --cluster default --service-name extractor --task-definition extractor:1
```

## Environment Variables

### Required
- `API_KEY`: API key for authentication
- `JWT_SECRET`: Secret key for JWT tokens

### Optional
- `GOOGLE_VISION_API_KEY`: For Google Vision OCR
- `MOSIP_BASE_URL`: MOSIP server URL
- `MOSIP_CLIENT_ID`: MOSIP client ID
- `MOSIP_SECRET`: MOSIP secret key

## Security Considerations

1. **Production Checklist**:
- [ ] Change all default passwords and keys
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Regular security updates

2. **API Security**:
- Use strong JWT secrets
- Implement request signing for sensitive endpoints
- Regular token rotation
- IP whitelisting for admin endpoints

## Monitoring

1. **Health Checks**:
```bash
curl http://localhost:9000/health
curl http://localhost:7000/health
```

2. **Logs**:
- Backend logs: `./logs/extractor.log`
- MOSIP logs: `./mock_mosip/mock_db.sqlite`

3. **Metrics**:
- Response times
- Error rates
- OCR processing times
- Quality scores distribution

## Troubleshooting

### Common Issues

1. **OCR not working**:
```bash
# Install Tesseract
sudo apt-get install tesseract-ocr
# or
brew install tesseract
```

2. **Frontend not connecting**:
- Check CORS settings in backend
- Verify API_URL in frontend .env

3. **Docker issues**:
```bash
# Reset Docker
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Support

For issues or questions:
1. Check logs for error messages
2. Verify all dependencies are installed
3. Ensure environment variables are set correctly
4. Open an issue on GitHub with details