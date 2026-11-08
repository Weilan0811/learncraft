from enum import StrEnum


class AssetStatus(StrEnum):
    pending = "pending"
    generating = "generating"
    generated = "generated"
    failed = "failed"
    missing = "missing"
    retrying = "retrying"
