"""
Google Vertex AI service for LLM and embeddings
"""
import logging
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.cloud.aiplatform.gapic.schema.predict import instance
from app.core.config import settings

logger = logging.getLogger(__name__)


class VertexAIService:
    """Google Vertex AI service for LLM and embeddings"""
    
    def __init__(self):
        self.project_id = settings.gcp_project_id
        self.location = settings.vertex_ai_location
        self.model_name = settings.vertex_ai_model_name
        self.embedding_model = settings.vertex_ai_embedding_model
        
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        """Generate text using Vertex AI"""
        try:
            # Create prediction instance
            prediction_instance = instance.TextGenerationPredictionInstance(
                content=prompt,
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=0.8,
                top_k=40
            )
            
            # Create prediction request
            prediction_request = predict.PredictionRequest(
                instances=[prediction_instance]
            )
            
            # Get model endpoint
            model_endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_name}"
            
            # Make prediction
            response = aiplatform.Endpoint(model_endpoint).predict(
                instances=[prediction_instance]
            )
            
            # Extract generated text
            if response.predictions:
                generated_text = response.predictions[0].get("content", "")
                return generated_text
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Failed to generate text with Vertex AI: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Vertex AI"""
        try:
            # Create prediction instances
            prediction_instances = []
            for text in texts:
                instance_data = {
                    "content": text
                }
                prediction_instances.append(instance_data)
            
            # Create prediction request
            prediction_request = predict.PredictionRequest(
                instances=prediction_instances
            )
            
            # Get model endpoint
            model_endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.embedding_model}"
            
            # Make prediction
            response = aiplatform.Endpoint(model_endpoint).predict(
                instances=prediction_instances
            )
            
            # Extract embeddings
            embeddings = []
            if response.predictions:
                for prediction in response.predictions:
                    embedding = prediction.get("embeddings", {}).get("values", [])
                    embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings with Vertex AI: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Chat completion using Vertex AI"""
        try:
            # Format messages for Vertex AI
            prompt = self._format_messages_for_vertex_ai(messages)
            
            # Generate response
            response = self.generate_text(prompt, max_tokens)
            return response
            
        except Exception as e:
            logger.error(f"Failed to complete chat with Vertex AI: {e}")
            raise
    
    def _format_messages_for_vertex_ai(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Vertex AI input"""
        formatted_prompt = ""
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"
        
        return formatted_prompt.strip()
    
    def generate_rag_response(self, question: str, context: str, max_tokens: int = 1000) -> str:
        """Generate RAG response using Vertex AI"""
        try:
            prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context. If the answer is not found in the context, please say so."""
            
            response = self.generate_text(prompt, max_tokens)
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            raise


# Global instance
vertex_ai_service = VertexAIService()
