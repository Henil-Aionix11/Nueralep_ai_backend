"""AI service for generating RAG-powered responses using AWS Bedrock."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Sequence

import boto3
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from app.core.models.chat_message_model import ChatMessage
from app.web.settings import settings


class AIService:
    """Service for AI response generation using Bedrock + ChromaDB retrieval."""

    def __init__(self) -> None:
        self.model_arn = os.getenv(
            "BEDROCK_MODEL_ARN",
            "arn:aws:bedrock:us-east-1:912565471172:inference-profile/us.meta.llama3-2-1b-instruct-v1:0",
        )

        self.chroma_db_path = settings.CHROMA_DB_PATH
        self.chroma_collection_name = settings.CHROMA_COLLECTION_NAME
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.openai_api_key = settings.OPENAI_API_KEY
        

        self.client = self._init_bedrock_client()
        self.embedder: Optional[OpenAIEmbeddings] = None
        self.chroma_client: Optional[chromadb.PersistentClient] = None
        self.chroma_collection = None
        self._init_vector_resources()

    def _init_bedrock_client(self):
        try:
            client = boto3.client("bedrock-runtime", region_name="us-east-1")
            logger.info("AWS Bedrock client initialized")
            return client
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to initialize AWS Bedrock: {exc}")
            return None

    def _init_vector_resources(self) -> None:
        """Prepare embedding + Chroma resources."""
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is missing; RAG retrieval disabled.")
            return


        try:
            self.embedder = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=self.openai_api_key,
                request_timeout=60,
                max_retries=3,
            )
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_db_path),
                settings=Settings(allow_reset=False, anonymized_telemetry=False),
            )
            self.chroma_collection = self.chroma_client.get_collection(self.chroma_collection_name)
            logger.info("Loaded Chroma collection '%s'", self.chroma_collection_name)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to initialize ChromaDB resources: {exc}")
            self.chroma_collection = None

    def _format_history(self, chat_history: Optional[Sequence[ChatMessage]]) -> str:
        if not chat_history:
            return ""

        lines: List[str] = []
        for message in chat_history[-10:]:
            role = getattr(message, "role", None)
            content = getattr(message, "content", None)

            if role is None and isinstance(message, dict):
                role = message.get("role")
            if content is None and isinstance(message, dict):
                content = message.get("content")

            if not role or not content:
                continue

            prefix = "User" if role == "user" else "Assistant"
            lines.append(f"{prefix}: {content}")
        return "\n".join(lines)

    def _retrieve_context(self, question: str, history_text: str = "") -> List[str]:
        if not self.chroma_collection or not self.embedder:
            return []

        try:
            query_text = question
            query_embedding = self.embedder.embed_query(query_text)
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                include=["documents"],
            )
            documents = results.get("documents") or []
            if not documents:
                return []
            return documents[0]
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to retrieve context from Chroma: {exc}")
            return []

    def _compose_prompt(
        self,
        agent_name: str,
        user_message: str,
        history_text: str,
        context_chunks: List[str],
    ) -> str:
        context_text = "\n\n".join(
            f"[{idx + 1}] {chunk}" for idx, chunk in enumerate(context_chunks)
        ) if context_chunks else "No supporting context retrieved."

        prompt_sections = [
            "You are a knowledgeable SAP data migration and enterprise IT assistant. "
            "Always use only the provided factual context when answering. and need to return full Answer"
            "If the answer is not explicitly present, reply 'I do not have enough information.' Be accurate, brief."
            f"Context:\n{context_text}",
        ]

        if history_text:
            prompt_sections.append(f"Conversation history:\n{history_text}")

        prompt_sections.extend(
            [
                f"User message:\n{user_message}",
                
            ]
        )
        return "\n\n".join(prompt_sections)

    async def get_response(
        self,
        agent_name: str,
        user_message: str,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> str:
        if not self.client:
            return "Sorry, AI service is currently unavailable."

        history_text = self._format_history(chat_history)
        context_chunks = self._retrieve_context(user_message, history_text)
        prompt_text = self._compose_prompt(agent_name, user_message, history_text, context_chunks)
        try:
            response = self.client.converse(
                modelId=self.model_arn,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt_text}],
                    }
                ],
                inferenceConfig={
                    "temperature": 0.15,
                    "topP": 0.85
                },
                performanceConfig={"latency": "standard"},
            )

            output_items = response.get("output", {}).get("message", {}).get("content", [])
            combined = ""
            for item in output_items:
                if isinstance(item, dict):
                    combined += item.get("text", "")
                else:
                    combined += str(item)

            final_text = combined.strip()
            if not final_text:
                logger.warning("Bedrock returned an empty response.")
                return "I do not have enough information."

            logger.info("AI response generated via Bedrock + Chroma")
            return final_text

        except Exception as exc:
            logger.error(f"AI generation failed: {exc}")
            return "Sorry, I encountered an error processing your request."
