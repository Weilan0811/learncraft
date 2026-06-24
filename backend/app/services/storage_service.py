import hashlib
import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Protocol

from app.core.config import get_settings
from app.schemas.assets import AssetKind, AssetRecord


class StorageService(Protocol):
    def save_bytes(
        self,
        asset_id: str,
        filename: str,
        content: bytes,
        content_type: str,
        kind: AssetKind,
        metadata: dict[str, object] | None = None,
    ) -> AssetRecord:
        """Persist bytes and return the stored asset record."""
        ...

    def get_record(self, asset_id: str) -> AssetRecord | None:
        """Load a stored asset record."""
        ...

    def get_file_path(self, asset_id: str) -> Path | None:
        """Return the absolute path for a stored asset file."""
        ...

    def read_bytes(self, asset_id: str) -> bytes:
        """Read stored asset bytes."""
        ...


class LocalStorageService:
    _locks_guard: ClassVar[threading.Lock] = threading.Lock()
    _manifest_locks: ClassVar[dict[Path, threading.RLock]] = {}

    def __init__(self, storage_root: str | Path | None = None, public_base_url: str | None = None) -> None:
        settings = get_settings()
        self.storage_root = Path(storage_root or settings.storage_root)
        self.public_base_url = (public_base_url or settings.asset_public_base_url).rstrip("/")
        self.files_dir = self.storage_root / "files"
        self.manifest_path = self.storage_root / "manifest.json"
        self._manifest_lock = self._lock_for_manifest(self.manifest_path)

    def save_bytes(
        self,
        asset_id: str,
        filename: str,
        content: bytes,
        content_type: str,
        kind: AssetKind,
        metadata: dict[str, object] | None = None,
    ) -> AssetRecord:
        safe_asset_id = self._safe_identifier(asset_id)
        safe_filename = Path(filename).name
        suffix = Path(safe_filename).suffix
        stored_filename = f"{safe_asset_id}{suffix}"
        relative_path = f"files/{stored_filename}"

        self.files_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.storage_root / relative_path
        file_path.write_bytes(content)

        record = AssetRecord(
            asset_id=safe_asset_id,
            kind=kind,
            filename=safe_filename,
            content_type=content_type,
            byte_size=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            storage_path=relative_path,
            created_at=datetime.now(UTC).isoformat(),
            url=self.get_public_url(safe_asset_id),
            metadata=metadata or {},
        )
        with self._manifest_lock:
            manifest = self._load_manifest()
            manifest["assets"][safe_asset_id] = record.model_dump()
            self._write_manifest(manifest)
        return record

    def get_record(self, asset_id: str) -> AssetRecord | None:
        safe_asset_id = self._safe_identifier(asset_id)
        with self._manifest_lock:
            asset_data = self._load_manifest()["assets"].get(safe_asset_id)
        return AssetRecord.model_validate(asset_data) if asset_data else None

    def get_file_path(self, asset_id: str) -> Path | None:
        record = self.get_record(asset_id)
        if record is None:
            return None
        path = (self.storage_root / record.storage_path).resolve()
        root = self.storage_root.resolve()
        if root != path and root not in path.parents:
            return None
        return path if path.exists() else None

    def read_bytes(self, asset_id: str) -> bytes:
        path = self.get_file_path(asset_id)
        if path is None:
            raise FileNotFoundError(asset_id)
        return path.read_bytes()

    def get_public_url(self, asset_id: str) -> str:
        return f"{self.public_base_url}/{asset_id}/download"

    def _load_manifest(self) -> dict[str, dict[str, object]]:
        if not self.manifest_path.exists():
            return {"assets": {}}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict[str, dict[str, object]]) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def _lock_for_manifest(cls, manifest_path: Path) -> threading.RLock:
        key = manifest_path.resolve()
        with cls._locks_guard:
            if key not in cls._manifest_locks:
                cls._manifest_locks[key] = threading.RLock()
            return cls._manifest_locks[key]

    @staticmethod
    def _safe_identifier(value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError(f"Unsafe asset id: {value}")
        return value
