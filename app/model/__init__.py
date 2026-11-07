"""Model assembly, storage adapter facade, and CLI entrypoint for Muse integration."""
from app.model.adapter import create_adapter, dispatch_call, seed_synthetic_recplace_store
from app.model.versioning import VersionedModelService
from database.adapter import IngestionAdapter, LocalDocumentStore, MongoStorageBackend, StorageBackend
from database.importer import (
    CANONICALIZATION_PROTOCOL,
    IMPORTER_VERSION,
    MAPPING_VERSION,
    RawRecPlaceImporter,
    canonical_logical_record_digest,
    compute_multiset_digest,
)
from database.schema import (
    COLLECTIONS,
    DEFAULT_DATABASE_NAME,
    DEFAULT_ORGANIZATION_ID,
    FACT_TYPES,
    INDEX_SPECS,
    KNOWLEDGE_STATES,
    RAW_TABLES,
    SCHEMA_VERSION,
    SIGNAL_KINDS,
    SOURCE_TYPES,
    TARGET_Q_VALUES,
    ContractError,
    validate_quote_in_text,
)

__all__ = [
    "CANONICALIZATION_PROTOCOL",
    "COLLECTIONS",
    "ContractError",
    "DEFAULT_DATABASE_NAME",
    "DEFAULT_ORGANIZATION_ID",
    "FACT_TYPES",
    "IMPORTER_VERSION",
    "INDEX_SPECS",
    "IngestionAdapter",
    "KNOWLEDGE_STATES",
    "LocalDocumentStore",
    "MAPPING_VERSION",
    "MongoStorageBackend",
    "RAW_TABLES",
    "RawRecPlaceImporter",
    "SCHEMA_VERSION",
    "SIGNAL_KINDS",
    "SOURCE_TYPES",
    "StorageBackend",
    "TARGET_Q_VALUES",
    "VersionedModelService",
    "canonical_logical_record_digest",
    "compute_multiset_digest",
    "create_adapter",
    "dispatch_call",
    "seed_synthetic_recplace_store",
    "validate_quote_in_text",
]
