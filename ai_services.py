from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
import config
import json
import random
import re

class AIServices:
    def __init__(self):
        # Initialize Groq LLM only (no OpenAI fallback)
        self.groq_llm = None
        if hasattr(config, 'GROQ_API_KEY') and config.GROQ_API_KEY:
            try:
                self.groq_llm = ChatGroq(
                    model="llama3-8b-8192",  # Fast and capable model
                    temperature=0.7,
                    groq_api_key=config.GROQ_API_KEY
                )
            except Exception as e:
                print(f"Groq initialization failed: {e}")
                raise Exception("Groq API key is required. Please set GROQ_API_KEY in your environment.")
        
        if not self.groq_llm:
            raise Exception("Groq API key is required. Please set GROQ_API_KEY in your environment.")
        
        self.llm = self.groq_llm
        
        self.search_tool = DuckDuckGoSearchRun()
        self.agent = initialize_agent(
            [self.search_tool],
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False
        )

    def switch_groq_model(self, model_name):
        """Switch to a different Groq model if available"""
        if not hasattr(config, 'GROQ_API_KEY') or not config.GROQ_API_KEY:
            return False
            
        available_models = [
            "llama3-8b-8192",    # Fast, good for general tasks
            "llama3-70b-8192",   # High quality, slower
            "gemma2-9b-it"       # Good balance
        ]
        
        if model_name not in available_models:
            print(f"Model {model_name} not available. Using {available_models[0]}")
            model_name = available_models[0]
        
        try:
            self.groq_llm = ChatGroq(
                model=model_name,
                temperature=0.7,
                groq_api_key=config.GROQ_API_KEY
            )
            self.llm = self.groq_llm
            print(f"Switched to Groq model: {model_name}")
            return True
        except Exception as e:
            print(f"Failed to switch to {model_name}: {e}")
            return False

    def chunk_text(self, text, max_chunk_size=3000):
        """Split text into chunks that fit within Groq's token limits"""
        # More conservative estimation: 1 token ≈ 3 characters for safety
        max_chars = max_chunk_size * 3
        
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        current_chunk = ""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If we still have very large chunks, split them further
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > max_chars:
                # Split large chunks into smaller pieces
                words = chunk.split()
                current_piece = ""
                for word in words:
                    if len(current_piece) + len(word) + 1 <= max_chars:
                        current_piece += word + " "
                    else:
                        if current_piece:
                            final_chunks.append(current_piece.strip())
                        current_piece = word + " "
                if current_piece:
                    final_chunks.append(current_piece.strip())
            else:
                final_chunks.append(chunk)
        
        return final_chunks

    def generate_summary(self, transcript):
        """Generate a structured, blog-style summary from transcript using Groq with chunking"""
        try:
            chunks = self.chunk_text(transcript)
            
            summary_prompt = f"""
            Generate a detailed, blog-style summary from the following transcript. The summary should be well-structured with clear headings, key points, examples, and a conclusion.

            Transcript:
            {"".join(chunks)}

            Please use the following Markdown format:

            # [Engaging Title for the Video]

            ## 🚀 Overview
            [Provide a brief, engaging overview of the video's content in one or two paragraphs.]

            ## 📚 Topic 1: [Name of the First Topic]
            **Key Points:**
            - [Point 1]
            - [Point 2]
            
            **Examples:**
            - "[Direct quote or paraphrased example from the transcript]"
            - "[Another example]"

            ## 📚 Topic 2: [Name of the Second Topic]
            **Key Points:**
            - [Point 1]
            - [Point 2]

            **Examples:**
            - "[Direct quote or paraphrased example]"
            - "[Another example]"

            *(...add more topics as needed...)*

            ## 🏁 Conclusion
            [Summarize the main takeaways of the video and provide a concluding thought.]
            """

            if len(chunks) == 1:
                response = self.llm.invoke(summary_prompt)
                return response.content
            else:
                # If chunking is needed, process chunks and then combine
                chunk_summaries = []
                for i, chunk in enumerate(chunks):
                    chunk_prompt = f"""
                    Summarize this part of the transcript ({i+1}/{len(chunks)}):
                    {chunk}
                    Focus on main ideas, key points, and examples.
                    """
                    response = self.llm.invoke(chunk_prompt)
                    chunk_summaries.append(response.content)
                
                combined_summary = "\n\n".join(chunk_summaries)
                
                final_prompt = f"""
                Create a single, cohesive, blog-style summary from these partial summaries.

                Partial Summaries:
                {combined_summary}

                Use the same structured format as requested before (Overview, Topics with Key Points/Examples, Conclusion).
                """
                
                response = self.llm.invoke(final_prompt)
                return response.content
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            raise e

    def generate_mcq(self, summary, previous_questions=None):
        """Generate MCQ questions from summary using Groq with chunking"""
        try:
            # Extract topics for question generation
            topics = self.extract_topics_from_summary(summary)
            
            # Avoid repeating previous questions
            previous_topics = []
            if previous_questions:
                for q in previous_questions:
                    if 'topic' in q:
                        previous_topics.append(q['topic'])
            
            # Filter out used topics
            available_topics = [topic for topic in topics if topic not in previous_topics]
            
            if not available_topics:
                available_topics = topics  # Reset if all topics used
            
            selected_topic = random.choice(available_topics)
            
            # Split summary if it's too long
            summary_chunks = self.chunk_text(summary, max_chunk_size=2000)
            
            if len(summary_chunks) == 1:
                prompt = f"""
                Generate a MCQ about {selected_topic} from this summary:
                {summary}
                
                Return JSON:
                {{
                    "question": "Question text?",
                    "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
                    "correct_answer": "A",
                    "explanation": "Why correct",
                    "topic": "{selected_topic}"
                }}
                """
            else:
                # Use first chunk for question generation
                prompt = f"""
                Generate a MCQ about {selected_topic} from this summary part:
                {summary_chunks[0]}
                
                Return JSON:
                {{
                    "question": "Question text?",
                    "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
                    "correct_answer": "A",
                    "explanation": "Why correct",
                    "topic": "{selected_topic}"
                }}
                """
            
            response = self.llm.invoke(prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response if it contains markdown formatting
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                question_data = json.loads(content)
                return question_data
                
            except json.JSONDecodeError:
                # Fallback: create a simple question structure
                return {
                    "question": "Based on the video content, what is the main topic discussed?",
                    "options": {
                        "A": "Technology trends",
                        "B": "Business strategies", 
                        "C": "Educational methods",
                        "D": "Health and wellness"
                    },
                    "correct_answer": "A",
                    "explanation": "This is a fallback question. Please check the summary for the actual main topic.",
                    "topic": selected_topic
                }
                
        except Exception as e:
            print(f"Error generating MCQ: {e}")
            raise e

    def extract_topics_from_summary(self, summary):
        """Extract key topics from summary for MCQ generation using Groq with chunking"""
        try:
            # Split summary if it's too long
            summary_chunks = self.chunk_text(summary, max_chunk_size=2000)
            
            if len(summary_chunks) == 1:
                prompt = f"""
                Extract 5-8 key topics from this summary for MCQ generation:
                {summary}
                
                Return topics, one per line.
                """
            else:
                # Use first chunk for topic extraction
                prompt = f"""
                Extract 5-8 key topics from this summary part for MCQ generation:
                {summary_chunks[0]}
                
                Return topics, one per line.
                """
            
            response = self.llm.invoke(prompt)
            topics = [topic.strip() for topic in response.content.split('\n') if topic.strip()]
            return topics[:8]  # Limit to 8 topics
            
        except Exception as e:
            print(f"Error extracting topics: {e}")
            # Fallback topics
            return ["Main concepts", "Key details", "Important points", "Core ideas"]

    def chat_with_ai(self, message, context=""):
        """Chat with AI using Groq and web search with chunking"""
        try:
            if context:
                # Split context if it's too long
                context_chunks = self.chunk_text(context, max_chunk_size=2000)
                if len(context_chunks) > 1:
                    # Use first chunk if context is too long
                    context = context_chunks[0] + " [Content truncated due to length]"
                
                full_message = f"Context from video: {context}\n\nUser question: {message}"
            else:
                full_message = message
            
            response = self.agent.invoke({"input": full_message})
            return response["output"]
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"Sorry, I encountered an error: {str(e)}" 