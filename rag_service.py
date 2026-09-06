import os
import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from fastembed import TextEmbedding
from langchain_groq import ChatGroq
import config

class RAGService:
    """
    RAG Service for Video Transcriber & Summarizer.
    - Chunks transcripts keeping exact timestamp metadata.
    - Embeds text locally using FastEmbed (zero API key / zero cost).
    - Persists vectors locally using ChromaDB.
    - Answers user questions with grounded context and timestamped citations using Groq.
    """
    def __init__(self, persist_directory: str = "chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="video_transcripts",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize local FastEmbed model (BAAI/bge-small-en-v1.5)
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # Initialize Groq LLM
        self.llm = None
        if hasattr(config, 'GROQ_API_KEY') and config.GROQ_API_KEY:
            try:
                self.llm = ChatGroq(
                    model="openai/gpt-oss-20b",
                    temperature=0.2,
                    groq_api_key=config.GROQ_API_KEY
                )
            except Exception as e:
                print(f"Groq LLM init in RAGService failed: {e}")

    def parse_transcript_lines(self, transcript_text: str) -> List[Dict[str, Any]]:
        """Parse raw transcript lines like '[00:00:01 - 00:00:05] Hello world'"""
        lines = transcript_text.strip().split('\n')
        segments = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = re.match(r'\[(.*?) - (.*?)\] (.*)', line)
            if match:
                start_ts, end_ts, text = match.groups()
                segments.append({
                    "start": start_ts,
                    "end": end_ts,
                    "text": text.strip()
                })
            else:
                segments.append({
                    "start": "00:00",
                    "end": "00:00",
                    "text": line
                })
        return segments

    def chunk_transcript(
        self, 
        video_id: str, 
        transcript_text: str, 
        target_chunk_words: int = 150, 
        overlap_segments: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Group timestamped segments into coherent chunks with overlap,
        preserving start_time and end_time metadata.
        """
        segments = self.parse_transcript_lines(transcript_text)
        if not segments:
            return []

        chunks = []
        i = 0
        chunk_idx = 0

        while i < len(segments):
            current_texts = []
            start_ts = segments[i]["start"]
            end_ts = segments[i]["end"]
            word_count = 0

            j = i
            while j < len(segments) and (word_count < target_chunk_words or len(current_texts) == 0):
                seg = segments[j]
                current_texts.append(seg["text"])
                end_ts = seg["end"]
                word_count += len(seg["text"].split())
                j += 1

            chunk_text = " ".join(current_texts).strip()
            if chunk_text:
                chunks.append({
                    "id": f"{video_id}_chunk_{chunk_idx}",
                    "video_id": str(video_id),
                    "chunk_index": chunk_idx,
                    "start_time": start_ts,
                    "end_time": end_ts,
                    "text": chunk_text
                })
                chunk_idx += 1

            # Advance with overlap
            advance_step = max(1, (j - i) - overlap_segments)
            i += advance_step

        return chunks

    def index_transcript(self, video_id: str, transcript_text: str) -> int:
        """
        Index transcript chunks into ChromaDB with FastEmbed embeddings.
        Deletes any previous chunks for the same video_id first.
        """
        try:
            # Delete existing chunks for this video if re-indexing
            self.delete_video_index(video_id)
            
            chunks = self.chunk_transcript(video_id, transcript_text)
            if not chunks:
                return 0

            texts = [c["text"] for c in chunks]
            # Generate embeddings locally via FastEmbed
            embeddings = list(self.embedding_model.embed(texts))
            embeddings = [emb.tolist() for emb in embeddings]

            ids = [c["id"] for c in chunks]
            metadatas = [{
                "video_id": c["video_id"],
                "chunk_index": c["chunk_index"],
                "start_time": c["start_time"],
                "end_time": c["end_time"]
            } for c in chunks]

            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"[RAG] Successfully indexed {len(chunks)} chunks for video {video_id}")
            return len(chunks)
        except Exception as e:
            print(f"[RAG] Error indexing transcript in RAG: {e}")
            raise e

    def retrieve(
        self, 
        query: str, 
        video_id: Optional[str] = None, 
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a user query."""
        if not query.strip():
            return []

        # Generate query embedding
        query_embedding = list(self.embedding_model.embed([query]))[0].tolist()

        where_clause = {"video_id": str(video_id)} if video_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        retrieved_chunks = []
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0]*len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                retrieved_chunks.append({
                    "text": doc,
                    "start_time": meta.get("start_time", "00:00"),
                    "end_time": meta.get("end_time", "00:00"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "video_id": meta.get("video_id", ""),
                    "score": round(1 - dist, 4) if dist is not None else 1.0
                })
        return retrieved_chunks

    def answer_question(
        self, 
        query: str, 
        video_id: Optional[str] = None, 
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        RAG Q&A pipeline:
        1. Retrieve top-k relevant timestamped segments.
        2. Build context string with explicit timestamp references.
        3. Query Groq LLM to provide an accurate answer with clickable timestamp citations.
        """
        if not self.llm:
            return {
                "answer": "Groq LLM is not initialized. Please verify your GROQ_API_KEY.",
                "sources": []
            }

        sources = self.retrieve(query, video_id=video_id, top_k=top_k)
        if not sources:
            return {
                "answer": "No relevant transcript context found in this video for your question.",
                "sources": []
            }

        context_blocks = []
        for i, s in enumerate(sources, 1):
            context_blocks.append(
                f"[Source {i}] Timestamp: [{s['start_time']} - {s['end_time']}]\nContent: {s['text']}"
            )
        context_str = "\n\n".join(context_blocks)

        prompt = f"""You are an intelligent Video Assistant. Answer the user's question accurately based ONLY on the provided video transcript excerpts below.

Video Transcript Excerpts:
---------------------
{context_str}
---------------------

Instructions:
- Provide a clear, direct, and helpful answer.
- Always cite the relevant timestamp range (e.g. `[02:15 - 02:45]`) when referencing specific facts or explanations from the video.
- If the answer cannot be determined from the transcript excerpts, politely state that the video does not cover that specific detail.

User Question: {query}

Answer:"""

        try:
            response = self.llm.invoke(prompt)
            return {
                "answer": response.content,
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": sources
            }

    def delete_video_index(self, video_id: str):
        """Remove all chunks associated with a video_id from the vector store."""
        try:
            self.collection.delete(where={"video_id": str(video_id)})
        except Exception:
            pass
