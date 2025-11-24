"""Local ingestion utility for populating ChromaDB with SAP knowledge.

The script reads the bundled knowledge sources (QnA + Neo4j training data),
generates OpenAI embeddings, and persists them inside a Chroma collection.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.web.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILES = [
    BASE_DIR / "QnA Training Data (1).txt",
    BASE_DIR / "neo4j_training_data (1).jsonl",
]
DEFAULT_CHROMA_PATH = BASE_DIR / "chroma_db"
DEFAULT_COLLECTION = "sap_migration_knowledge"
DEFAULT_EMBED_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_BATCH_SIZE = 100


def load_json_records(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL/JSON data from disk."""
    if not file_path.exists():
        logger.error("File %s does not exist", file_path)
        return []

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        logger.warning("File %s is empty", file_path.name)
        return []

    # Full JSON array
    if content[0] in ("[", "{"):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                logger.info("Loaded %d records from %s", len(parsed), file_path.name)
                return parsed
            elif isinstance(parsed, dict):
                logger.info("Loaded single JSON document from %s", file_path.name)
                return [parsed]
        except json.JSONDecodeError:
            # fall back to per-line parsing
            pass

    docs: List[Dict[str, Any]] = []
    for idx, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            docs.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Line %s in %s is not valid JSON, skipping", idx, file_path.name)

    logger.info("Loaded %d records from %s", len(docs), file_path.name)
    return docs


def chunk_documents(documents: Sequence[Dict[str, Any]], filename: str) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    """Convert heterogeneous documents into embedding-ready chunks."""
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for idx, doc in enumerate(documents):
        if "question" in doc and "answer" in doc:
            text = f"Question: {doc.get('question','').strip()}\n\nAnswer: {doc.get('answer','').strip()}"
            metadata = {
                "source": "qna",
                "doc_type": "question_answer",
                "filename": filename,
                "intent": doc.get("intent", ""),
                "category": doc.get("category", ""),
                "domain": doc.get("domain", ""),
                "entities": ",".join(doc.get("entities", [])) if isinstance(doc.get("entities"), list) else doc.get("entities", ""),
            }
            doc_id = f"qna_{Path(filename).stem}_{idx}"
        elif "prompt" in doc and "completion" in doc:
            text = f"Prompt: {doc.get('prompt','').strip()}\n\nCompletion: {doc.get('completion','').strip()}"
            metadata = {
                "source": "neo4j_graph",
                "doc_type": "graph_training",
                "filename": filename,
            }
            doc_id = f"neo4j_{Path(filename).stem}_{idx}"
        else:
            text = json.dumps(doc, ensure_ascii=False)
            metadata = {
                "source": "generic",
                "doc_type": "json_document",
                "filename": filename,
            }
            doc_id = f"generic_{Path(filename).stem}_{idx}"

        texts.append(text)
        metadatas.append(metadata)
        ids.append(doc_id)

    logger.info("Prepared %d chunks from %s", len(texts), filename)
    return texts, metadatas, ids


class EmbeddingManager:
    """Handles OpenAI embedding generation with retries."""

    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        self._embeddings = None

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=self.api_key,
                request_timeout=60,
                max_retries=3,
            )
        return self._embeddings

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            logger.warning("No texts passed to embed_documents")
            return []
        logger.info("Generating embeddings for %d texts", len(texts))
        return self.embeddings.embed_documents(texts)


class ChromaDBManager:
    """Wraps PersistentClient calls."""

    def __init__(self, db_path: Path):
        db_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
        )
        self.collection = None

    def get_or_create_collection(self, name: str):
        try:
            self.collection = self.client.get_collection(name=name)
            logger.info("Using existing Chroma collection '%s'", name)
        except Exception:
            self.collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Created new Chroma collection '%s'", name)

    def add_documents(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], ids: List[str], batch_size: int = 5000):
        if not self.collection:
            raise RuntimeError("Chroma collection has not been initialized")
        total = len(texts)
        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            self.collection.upsert(
                documents=texts[start:end],
                embeddings=embeddings[start:end],
                metadatas=metadatas[start:end],
                ids=ids[start:end],
            )
            logger.info("Persisted batch %d-%d", start, end - 1)

    def stats(self) -> Dict[str, Any]:
        if not self.collection:
            return {}
        return {
            "total_documents": self.collection.count(),
            "sample_ids": self.collection.peek(limit=3).get("ids", []),
        }


def ingest_to_chromadb(openai_api_key: str, files: Sequence[Path], chroma_path: Path, collection: str, batch_size: int) -> bool:
    all_texts: List[str] = []
    all_metadatas: List[Dict[str, Any]] = []
    all_ids: List[str] = []

    for file_path in files:
        docs = load_json_records(file_path)
        if not docs:
            logger.warning("No valid records found in %s, skipping", file_path.name)
            continue
        texts, metadatas, ids = chunk_documents(docs, file_path.name)
        all_texts.extend(texts)
        all_metadatas.extend(metadatas)
        all_ids.extend(ids)

    if not all_texts:
        logger.error("No documents prepared for ingestion. Aborting.")
        return False

    embedding_mgr = EmbeddingManager(DEFAULT_EMBED_MODEL, openai_api_key)

    def batched_embeddings() -> List[List[float]]:
        embeddings: List[List[float]] = []
        total = len(all_texts)
        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            logger.info("Embedding batch %d/%d", (start // batch_size) + 1, ((total - 1) // batch_size) + 1)
            batch = all_texts[start:end]
            embeddings.extend(embedding_mgr.embed_documents(batch))
        return embeddings

    embeddings = batched_embeddings()
    if len(embeddings) != len(all_texts):
        logger.error("Embedding count mismatch (%d embeddings vs %d texts)", len(embeddings), len(all_texts))
        return False

    chroma_mgr = ChromaDBManager(chroma_path)
    chroma_mgr.get_or_create_collection(collection)
    chroma_mgr.add_documents(all_texts, embeddings, all_metadatas, all_ids)
    logger.info("Ingestion complete: %s", chroma_mgr.stats())
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest local training data into ChromaDB.")
    parser.add_argument(
        "--files",
        nargs="+",
        default=[str(path) for path in DEFAULT_DATA_FILES],
        help="List of JSON/JSONL files to ingest.",
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_CHROMA_PATH),
        help="Directory where the Chroma database is stored.",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Name of the Chroma collection to use.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of texts to embed per batch.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    openai_api_key = settings.OPENAI_API_KEY
    if not openai_api_key:
        raise SystemExit("OPENAI_API_KEY must be set in the environment.")

    file_paths = [Path(path).resolve() for path in args.files]
    success = ingest_to_chromadb(
        openai_api_key=openai_api_key,
        files=file_paths,
        chroma_path=Path(args.db_path).resolve(),
        collection=args.collection,
        batch_size=args.batch_size,
    )

    if success:
        logger.info("Ingestion finished successfully.")
    else:
        logger.error("Ingestion failed. Check logs for details.")


if __name__ == "__main__":
    main()

