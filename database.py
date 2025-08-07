import pymongo
from datetime import datetime
from bson import ObjectId
import config

class Database:
    def __init__(self):
        try:
            # Add connection timeout and retry settings
            self.client = pymongo.MongoClient(
                config.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connect timeout
                socketTimeoutMS=10000,          # 10 second socket timeout
                maxPoolSize=10,
                retryWrites=True
            )
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[config.MONGO_DB]
            self.videos = self.db.videos
            self.transcripts = self.db.transcripts
            self.summaries = self.db.summaries
            self.mcqs = self.db.mcqs
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("💡 Please check your MONGO_URI in .env file")
            print("💡 For local MongoDB: mongodb://localhost:27017/")
            print("💡 For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/")
            # Create a mock database for testing
            self.client = None
            self.db = None
            self.videos = None
            self.transcripts = None
            self.summaries = None
            self.mcqs = None
    
    def save_video(self, title, filename, s3_url, duration=None):
        """Save video metadata"""
        if not self.client:
            raise Exception("MongoDB not connected. Please check your connection settings.")
        
        video_doc = {
            "title": title,
            "filename": filename,
            "s3_url": s3_url,
            "duration": duration,
            "upload_date": datetime.now(),
            "status": "uploaded"
        }
        result = self.videos.insert_one(video_doc)
        return str(result.inserted_id)
    
    def get_all_videos(self):
        """Get all videos"""
        if not self.client:
            return []
        
        return list(self.videos.find().sort("upload_date", -1))
    
    def get_video_by_id(self, video_id):
        """Get video by ID"""
        if not self.client:
            return None
        
        return self.videos.find_one({"_id": ObjectId(video_id)})
    
    def save_transcript(self, video_id, transcript_data):
        """Save transcript with timestamps"""
        transcript_doc = {
            "video_id": ObjectId(video_id),
            "transcript": transcript_data,
            "created_at": datetime.now()
        }
        result = self.transcripts.insert_one(transcript_doc)
        return str(result.inserted_id)
    
    def get_transcript(self, video_id):
        """Get transcript for a video"""
        return self.transcripts.find_one({"video_id": ObjectId(video_id)})
    
    def save_summary(self, video_id, summary_data):
        """Save AI-generated summary"""
        summary_doc = {
            "video_id": ObjectId(video_id),
            "summary": summary_data,
            "created_at": datetime.now()
        }
        result = self.summaries.insert_one(summary_doc)
        return str(result.inserted_id)
    
    def get_summary(self, video_id):
        """Get summary for a video"""
        return self.summaries.find_one({"video_id": ObjectId(video_id)})
    
    def save_mcq(self, video_id, question_data):
        """Save MCQ question"""
        mcq_doc = {
            "video_id": ObjectId(video_id),
            "question": question_data,
            "created_at": datetime.now()
        }
        result = self.mcqs.insert_one(mcq_doc)
        return str(result.inserted_id)
    
    def get_mcqs(self, video_id):
        """Get all MCQs for a video"""
        return list(self.mcqs.find({"video_id": ObjectId(video_id)}))
    
    def update_video_status(self, video_id, status):
        """Update video processing status"""
        self.videos.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"status": status}}
        ) 