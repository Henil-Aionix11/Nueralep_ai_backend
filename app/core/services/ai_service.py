"""AI service for generating RAG-powered responses using AWS Bedrock."""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Sequence, Union

import boto3
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from loguru import logger
from openai import OpenAI

from app.core.models.chat_message_model import ChatMessage
from app.web.settings import settings
from app.core.prompt.prompt import CONTEXTUAL_PROMPT


ChatContextMessage = Union[ChatMessage, Dict[str, str]]


class AIService:
    """Service for AI response generation using Bedrock + ChromaDB retrieval."""

    def __init__(self) -> None:
        self.model_arn = "arn:aws:bedrock:us-east-1:912565471172:inference-profile/us.meta.llama3-2-3b-instruct-v1:0"

        self.chroma_db_path = settings.CHROMA_DB_PATH
        self.chroma_collection_name = settings.CHROMA_COLLECTION_NAME
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.openai_api_key = settings.OPENAI_API_KEY
        self.contextual_model = getattr(settings, "OPENAI_CONTEXT_MODEL", "gpt-4o-mini")
        

        self.client = self._init_bedrock_client()
        self.embedder: Optional[OpenAIEmbeddings] = None
        self.chroma_client: Optional[chromadb.PersistentClient] = None
        self.chroma_collection = None
        self.openai_context_client: Optional[OpenAI] = None

        self._init_openai_context_client()
        self._init_vector_resources()

    def _init_bedrock_client(self):
        try:
            client = boto3.client("bedrock-runtime", region_name="us-east-1")
            logger.info("AWS Bedrock client initialized")
            return client
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to initialize AWS Bedrock: {exc}")
            return None

    def _init_openai_context_client(self) -> None:
        """Initialize OpenAI client for contextual question generation."""
        if not self.openai_api_key:
            return

        try:
            self.openai_context_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for contextual questions")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to initialize OpenAI client: {exc}")
            self.openai_context_client = None

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

    def _normalize_chat_context(
        self, chat_history: Optional[Sequence[ChatContextMessage]]
    ) -> List[Dict[str, str]]:
        if not chat_history:
            return []

        normalized: List[Dict[str, str]] = []
        for message in list(chat_history)[-10:]:
            role = getattr(message, "role", None)
            content = getattr(message, "content", None)

            if role is None and isinstance(message, dict):
                role = message.get("role")
            if content is None and isinstance(message, dict):
                content = message.get("content")

            if not role or not content:
                continue

            normalized.append(
                {
                    "role": str(role).lower(),
                    "content": str(content),
                }
            )
        return normalized

    def generate_contextual_question(
        self,
        user_query: str,
        chat_context: Optional[Sequence[ChatContextMessage]] = None,
    ) -> str:
        """Generate a standalone question using the chat context."""

        if not user_query:
            return ""

        normalized_context = self._normalize_chat_context(chat_context)
        if not normalized_context:
            logger.info("[CONTEXTUAL] No chat context provided, returning original query")
            return user_query

        if not self.openai_context_client or not self.contextual_model:
            logger.warning(
                "[CONTEXTUAL] OpenAI client not available, using original query"
            )
            return user_query

        try:
            logger.info("[CONTEXTUAL] Starting contextual question generation...")
            start_time = time.time()

            chat_history_text = "\n".join(
                f"{msg['role']}: {msg['content']}" for msg in normalized_context
            )
            user_prompt = (
                f"Chat History:\n{chat_history_text}\n\nLatest Question: {user_query}"
            )

            api_start = time.time()
            response = self.openai_context_client.chat.completions.create(
                model=self.contextual_model,
                messages=[
                    {"role": "system", "content": CONTEXTUAL_PROMPT.strip()},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                timeout=40,
            )
            api_duration = time.time() - api_start
            logger.info(f"[CONTEXTUAL] OpenAI API call completed in {api_duration:.2f}s")

            if hasattr(response, "usage") and response.usage:
                logger.info(
                    "[CONTEXTUAL] Token usage → prompt: %s, completion: %s, total: %s",
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    response.usage.total_tokens,
                )

            choices = getattr(response, "choices", None) or []
            if not choices or not getattr(choices[0], "message", None):
                logger.warning(
                    "[CONTEXTUAL] No choices returned from OpenAI, using original query"
                )
                return user_query

            contextual_question = (choices[0].message.content or "").strip()
            if not contextual_question:
                logger.warning(
                    "[CONTEXTUAL] Empty contextual question received, using original query"
                )
                return user_query

            total_duration = time.time() - start_time

            logger.info(f"[CONTEXTUAL] COMPLETED in {total_duration:.2f}s")
            logger.info(f"[CONTEXTUAL] Original query: {user_query}")
            logger.info(f"[CONTEXTUAL] Contextual question: {contextual_question}")

            return contextual_question
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                f"[CONTEXTUAL] ERROR generating contextual question: {exc}", exc_info=True
            )
            return user_query

    def _retrieve_context(self, question: str) -> List[str]:
        if not self.chroma_collection or not self.embedder:
            return []

        try:
            query_text = question
            query_embedding = self.embedder.embed_query(query_text)
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=['documents', 'distances'],
            )
            documents_outer = results.get("documents") or []
            distances_outer = results.get("distances") or []

            print("**********************************")
            print(f"results: {results}")

            if not documents_outer or not distances_outer:
                return []

            docs = documents_outer[0]
            dists = distances_outer[0]

            threshold = 0.55
            filtered = []

            for doc_text, raw_dist in zip(docs, dists):
                numeric_dist = None

                # Inline flattening / numeric extraction (stack-based)
                try:
                    stack = [raw_dist]
                    numeric_candidates = []
                    while stack:
                        item = stack.pop()
                        # direct numeric
                        if isinstance(item, (int, float)):
                            numeric_candidates.append(float(item))
                        # numeric-looking string
                        elif isinstance(item, str):
                            try:
                                numeric_candidates.append(float(item))
                            except Exception:
                                # not numeric, skip
                                continue
                        # iterable (list/tuple) -> push elements to stack to flatten
                        elif isinstance(item, (list, tuple)):
                            for elem in item:
                                stack.append(elem)
                        else:
                            # unknown type: skip
                            continue

                    if numeric_candidates:
                        # choose minimum numeric value found (closest)
                        numeric_dist = min(numeric_candidates)
                except Exception:
                    # Defensive: if anything unexpected happens, leave numeric_dist as None
                    numeric_dist = None

                # If we couldn't parse a numeric distance, skip this chunk
                if numeric_dist is None:
                    logger.debug("Skipping chunk due to non-numeric distance: %r", raw_dist)
                    continue

                # Keep when numeric_dist >= threshold (per your requirement)
                if numeric_dist <= threshold:
                    filtered.append(doc_text)
                else:
                    logger.debug("Filtered out chunk with distance %s < %s", numeric_dist, threshold)

            print(f"filtered: {filtered}")
            return filtered

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to retrieve context from Chroma: {exc}")
            return []

    def _compose_prompt(
        self,
        contextual_question: str,
        context_chunks: List[str],
        agent_name: Optional[str] = None,
    ) -> str:
        context_text = "\n\n".join(
            f"[{idx + 1}] {chunk}" for idx, chunk in enumerate(context_chunks)
        ) if context_chunks else "No supporting context retrieved."

       

        prompt_sections = [
            "You are a knowledgeable SAP data migration and enterprise IT assistant. "
            "Always use only the provided factual context when answering. and need to return full Answer"
            "If the context is not enough to answer the provided question, return with 'I don't have enough context to answer that question'"
            f"Context:\n{context_text}",
            f"User question:\n{contextual_question}",
        ]
        return "\n\n".join(prompt_sections)

    async def get_response(
        self,
        agent_name: str,
        user_message: str,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> str:
        if not self.client:
            return "Sorry, AI service is currently unavailable."

        contextual_question = self.generate_contextual_question(
            user_message, chat_history
        )
        context_chunks = self._retrieve_context(contextual_question)

        if not context_chunks:
            return "I don't have enough context to answer that question."
        
        prompt_text = self._compose_prompt(
            contextual_question=contextual_question,
            context_chunks=context_chunks,
            agent_name=agent_name,
        )
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
