"""Self-hosted knowledge base module.

Relative-independent from the backend app: corpus lives in ``knowledge/raw/``,
retrieval engine in ``knowledge/engine/``, evaluation in ``knowledge/eval/``.
The backend consumes it through ``backend/app/services/local_kb_service.py``,
which adapts this engine to the RAGService contract.
"""
