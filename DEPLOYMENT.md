# 🚀 Deployment Guide

This guide will help you deploy your Video Transcriber & Summarizer application for free or at minimal cost.

## 🆓 Free Deployment Options

### 1. Streamlit Cloud (Recommended)

**Pros:**

- ✅ Completely free
- ✅ Easy deployment
- ✅ Automatic updates
- ✅ Custom domain support

**Cons:**

- ❌ Limited resources (1GB RAM)
- ❌ No persistent storage
- ❌ Sleep after inactivity

#### Setup Steps:

1. **Prepare Your Repository**

   ```bash
   # Ensure all files are committed
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Streamlit Cloud Account**

   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign up with GitHub
   - Connect your repository

3. **Configure Deployment**

   - **Repository**: Select your repo
   - **Branch**: `main`
   - **Main file path**: `main.py`
   - **Python version**: 3.9

4. **Set Environment Variables**
   In Streamlit Cloud dashboard, add these secrets:

   ```toml
   [secrets]
   MONGO_URI = "your_mongodb_connection_string"
   AWS_ACCESS_KEY_ID = "your_aws_access_key"
   AWS_SECRET_ACCESS_KEY = "your_aws_secret_key"
   AWS_REGION = "us-east-1"
   S3_BUCKET_NAME = "your_bucket_name"
   OPENAI_API_KEY = "your_openai_api_key"
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at `https://your-app-name.streamlit.app`

### 2. Render (Alternative Free Option)

**Pros:**

- ✅ Free tier available
- ✅ More resources than Streamlit Cloud
- ✅ Custom domains

**Cons:**

- ❌ Sleeps after 15 minutes of inactivity
- ❌ Slower cold starts

#### Setup Steps:

1. **Create Render Account**

   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**

   - Connect your repository
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run main.py --server.port $PORT --server.address 0.0.0.0`

3. **Set Environment Variables**
   Add the same environment variables as Streamlit Cloud

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment

### 3. Railway (Paid but Affordable)

**Pros:**

- ✅ $5/month after free tier
- ✅ No sleep
- ✅ Good performance
- ✅ Easy deployment

**Setup:**

- Similar to Render but with better performance

## 🔧 Required Services Setup

### MongoDB Atlas (Free Database)

1. **Create Account**

   - Go to [mongodb.com/atlas](https://mongodb.com/atlas)
   - Sign up for free tier

2. **Create Cluster**

   - Choose "Free" tier
   - Select cloud provider and region
   - Create cluster

3. **Set Up Database**

   - Create database user
   - Get connection string
   - Add to environment variables

4. **Network Access**
   - Add `0.0.0.0/0` for all IPs (or specific IPs for security)

### AWS S3 (Free Tier)

1. **Create AWS Account**

   - Sign up at [aws.amazon.com](https://aws.amazon.com)
   - Free tier includes 5GB storage

2. **Create S3 Bucket**

   ```bash
   # Bucket name must be unique globally
   aws s3 mb s3://your-unique-bucket-name
   ```

3. **Configure CORS**

   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
       "AllowedOrigins": ["*"],
       "ExposeHeaders": []
     }
   ]
   ```

4. **Create IAM User**
   - Create user with S3 access
   - Generate access keys
   - Add to environment variables

### OpenAI API

1. **Sign Up**

   - Go to [openai.com](https://openai.com)
   - Create account

2. **Get API Key**

   - Go to API Keys section
   - Create new key
   - Add funds to account (pay-per-use)

3. **Add to Environment**
   - Copy API key to environment variables

## 📊 Cost Analysis

### Free Tier Limits

| Service             | Free Limit  | Cost After        |
| ------------------- | ----------- | ----------------- |
| **Streamlit Cloud** | Unlimited   | N/A               |
| **MongoDB Atlas**   | 512MB       | $9/month          |
| **AWS S3**          | 5GB         | $0.023/GB         |
| **OpenAI**          | Pay-per-use | ~$0.01-0.05/video |

### Monthly Costs (Typical Usage)

| Usage          | Transcription | Storage | API Calls | Total |
| -------------- | ------------- | ------- | --------- | ----- |
| **10 videos**  | $0            | $0.23   | $0.50     | $0.73 |
| **50 videos**  | $0            | $1.15   | $2.50     | $3.65 |
| **100 videos** | $0            | $2.30   | $5.00     | $7.30 |

## 🚀 Production Deployment

### AWS (Recommended for Production)

1. **EC2 Instance**

   ```bash
   # Launch t3.medium instance
   # Install Python, FFmpeg, MongoDB
   sudo apt update
   sudo apt install python3-pip ffmpeg
   ```

2. **RDS Database**

   - Create PostgreSQL or MySQL instance
   - Update database connection

3. **Load Balancer**

   - Set up Application Load Balancer
   - Configure SSL certificate

4. **Auto Scaling**
   - Configure auto-scaling groups
   - Set up monitoring

### Google Cloud Platform

1. **Compute Engine**

   - Similar to AWS EC2
   - Use preemptible instances for cost savings

2. **Cloud SQL**

   - Managed database service
   - Automatic backups

3. **Cloud Storage**
   - Alternative to S3
   - Better integration with GCP

## 🔒 Security Considerations

### Environment Variables

- Never commit `.env` files
- Use platform secrets management
- Rotate keys regularly

### Database Security

- Use strong passwords
- Enable SSL connections
- Restrict network access

### API Security

- Monitor API usage
- Set rate limits
- Use API keys securely

## 📈 Performance Optimization

### Caching

```python
@st.cache_resource
def expensive_function():
    # Results cached across sessions
    pass
```

### Database Indexing

```javascript
// MongoDB indexes for better performance
db.videos.createIndex({ upload_date: -1 });
db.transcripts.createIndex({ video_id: 1 });
```

### CDN for Videos

- Use CloudFront (AWS) or Cloud CDN (GCP)
- Reduce video loading times
- Lower bandwidth costs

## 🐛 Common Deployment Issues

### Memory Issues

```python
# Add to main.py for memory optimization
import gc
gc.collect()
```

### Timeout Issues

```python
# Increase timeout for long operations
st.set_option('server.maxUploadSize', 200)
```

### CORS Issues

```python
# Add CORS headers if needed
st.set_option('server.enableCORS', True)
```

## 📞 Support

### Deployment Help

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)

### Service Support

- [MongoDB Atlas Support](https://docs.atlas.mongodb.com)
- [AWS S3 Docs](https://docs.aws.amazon.com/s3)
- [OpenAI API Docs](https://platform.openai.com/docs)

---

**Ready to deploy? Start with Streamlit Cloud for the easiest free deployment!**
