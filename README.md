# 🎥 Video Transcriber & Summarizer

A comprehensive web application that transforms videos into interactive learning experiences using AI-powered transcription, summarization, and practice questions.

## ✨ Features

### 🎬 Video Management

- **Upload videos** with custom titles
- **Video list** with search and filtering
- **Cloud storage** using AWS S3
- **Multiple video formats** support

### 📝 AI-Powered Transcription

- **Accurate transcription** using OpenAI Whisper
- **Timestamp synchronization** for easy navigation
- **Real-time processing** with progress tracking

### 📋 Intelligent Summarization

- **Structured summaries** with headings and bullet points
- **Key point extraction** from video content
- **Downloadable summaries** in text format
- **Automatic chunking** for large content to handle token limits

## 🏗️ Architecture

```
Frontend (Streamlit) → Backend Services → External APIs
├── Multi-page UI     ├── MongoDB       ├── Groq LLM
├── Video Player      ├── AWS S3        ├── OpenAI Whisper
├── Interactive Tabs  ├── Local Whisper ├── LangChain
└── Real-time Updates └── AI Services   └── Web Search
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **MongoDB** (local or cloud)
- **AWS S3** bucket
- **Groq API** key (free tier available)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd video-transcriber
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   cp env_example.txt .env
   # Edit .env with your credentials
   ```

4. **Configure services**

   - Set up MongoDB database
   - Create AWS S3 bucket
   - Get Groq API key (free tier available)

5. **Run the application**

   ```bash
   streamlit run main.py
   ```

   **Note**: The application is configured to support video uploads up to 500MB. This is set in `.streamlit/config.toml`.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

### File Upload Configuration

The application supports video uploads up to **500MB** by default. This is configured in `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 500
```

To change this limit, modify the `maxUploadSize` value in the config file or set it via command line:

```bash
streamlit run main.py --server.maxUploadSize 1000  # For 1GB limit
```

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=video_transcriber

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_s3_bucket_name_here

# Groq Configuration (Required - Free tier available)
GROQ_API_KEY=your_groq_api_key_here
```

### Service Setup

#### MongoDB

- **Local**: Install MongoDB locally
- **Cloud**: Use MongoDB Atlas (free tier available)

#### AWS S3

1. Create an S3 bucket
2. Configure CORS for video streaming
3. Set up IAM user with S3 permissions

#### Groq

1. Sign up at [Groq](https://console.groq.com)
2. Get API key from dashboard
3. Free tier available with generous limits

## 📱 Usage

### 1. Upload Video

- Navigate to "Videos List" page
- Click "Upload Video" tab
- Enter video title and select file
- Wait for processing (transcription + summary)

### 2. View Video

- Click "Play" on any video in the list
- Video player opens with transcript sidebar
- Use tabs for Summary, Practice, and Chatbot

### 3. Practice Mode

- Click "Practice" tab
- Answer MCQ questions
- Get instant feedback and explanations
- Generate new questions with "Next Question"

### 4. AI Chatbot

- Click "Chatbot" tab
- Ask questions about the video or any topic
- Get AI responses with web search capability

## 🎯 Key Features Explained

### Multi-Page Navigation

- **Home**: Dashboard with stats and recent videos
- **Videos List**: Upload and manage videos
- **Play Video**: Interactive video viewing experience

### Video Processing Pipeline

1. **Upload** → AWS S3 storage
2. **Transcribe** → OpenAI Whisper (local)
3. **Summarize** → Groq LLM (with chunking for large content)
4. **Store** → MongoDB database

### Interactive UI Components

- **Video Player**: Fullscreen-capable with controls
- **Transcript Display**: Scrollable with timestamp highlighting
- **Practice System**: Dynamic MCQ generation with feedback
- **Chat Interface**: Real-time AI conversations

## 🚀 Deployment Options

### Free Deployment

- **Streamlit Cloud**: Easy deployment with free tier
- **Render**: Free tier with sleep after inactivity
- **Railway**: $5/month after free tier

### Production Deployment

- **AWS**: EC2 + RDS + S3
- **Google Cloud**: Compute Engine + Cloud SQL
- **Azure**: App Service + Cosmos DB

## 💰 Cost Analysis

### Free Tier Usage

- **Whisper**: $0 (local processing)
- **Groq**: $0 (free tier with generous limits)
- **MongoDB**: $0 (local) or free tier
- **S3**: ~$0.023 per GB stored

### Monthly Costs (100 videos)

- **Transcription**: $0 (local)
- **Summarization**: $0 (free tier)
- **Storage**: $2-10 (depending on video sizes)
- **Total**: $2-10/month

## 🔧 Customization

### Adding New Features

- **Custom AI models**: Modify `ai_services.py`
- **Additional video formats**: Update `config.py`
- **New practice types**: Extend practice tab
- **Enhanced UI**: Modify Streamlit components

### Performance Optimization

- **Caching**: Use `@st.cache_resource`
- **Async processing**: Background tasks
- **CDN**: CloudFront for video delivery
- **Database indexing**: Optimize queries

## 🐛 Troubleshooting

### Common Issues

1. **Whisper Installation**

   ```bash
   # Install FFmpeg first
   # Windows: Download from https://ffmpeg.org/
   # Mac: brew install ffmpeg
   # Linux: sudo apt install ffmpeg
   ```

2. **MongoDB Connection**

   - Check connection string
   - Ensure database exists
   - Verify network access

3. **S3 Upload Issues**

   - Verify AWS credentials
   - Check bucket permissions
   - Ensure CORS configuration

4. **Groq API Errors**
   - Check API key validity
   - Monitor rate limits
   - Large content is automatically chunked to avoid token limits

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for Whisper transcription
- **Groq** for fast LLM inference
- **Streamlit** for the web framework
- **LangChain** for AI agent capabilities
- **MongoDB** for database solution

## 📞 Support

For questions and support:

- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**Built with ❤️ using Streamlit, Groq, and modern AI technologies**
