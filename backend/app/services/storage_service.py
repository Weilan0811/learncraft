from typing import Protocol


class StorageService(Protocol):
    def save_bytes(self, path: str, content: bytes, content_type: str) -> str:
        """Persist bytes and return a public URL."""
        ...


class StubStorageService:
    def save_bytes(self, path: str, content: bytes, content_type: str) -> str:
        return f"/api/assets/{path}"
