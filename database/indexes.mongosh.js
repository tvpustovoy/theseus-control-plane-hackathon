// Explicit index setup for database `theseus_recplace` per database/INGESTION-CONTRACT.md v0.1
// and database/SCHEMA.md v0. Review target database and permissions before applying.

// 1. Ingestion Contract v0.1 collections
db.raw_records.createIndex(
  { organization_id: 1, record_key: 1 },
  { unique: true, name: "uniq_org_record_key" }
);
db.raw_records.createIndex(
  { organization_id: 1, import_run_id: 1, source_table: 1 },
  { name: "idx_org_import_run_table" }
);
db.raw_records.createIndex(
  { organization_id: 1, payload_sha256: 1 },
  { name: "idx_org_payload_sha256" }
);

db.import_runs.createIndex(
  { organization_id: 1, _id: 1, status: 1 },
  { name: "idx_org_import_run_status" }
);

db.sources.createIndex(
  { organization_id: 1, _id: 1, source_version: 1 },
  { unique: true, name: "uniq_org_source_version" }
);
db.sources.createIndex(
  { organization_id: 1, source_type: 1, _id: 1 },
  { name: "idx_org_source_type" }
);
db.sources.createIndex(
  { organization_id: 1, text_sha256: 1 },
  { name: "idx_org_source_text_sha256" }
);

db.source_chunks.createIndex(
  { organization_id: 1, source_id: 1, source_version: 1, chunk_id: 1 },
  { unique: true, name: "uniq_org_source_ver_chunk" }
);

db.extraction_runs.createIndex(
  { organization_id: 1, source_id: 1, source_version: 1, prompt_version: 1, model: 1, input_hash: 1 },
  { name: "idx_org_extraction_idempotency" }
);

db.claims.createIndex(
  { organization_id: 1, source_id: 1, chunk_id: 1, extraction_status: 1 },
  { name: "idx_org_source_chunk_status" }
);
db.claims.createIndex(
  { organization_id: 1, fact_type: 1, zone: 1, extraction_status: 1 },
  { name: "idx_org_fact_type_zone_status" }
);
db.claims.createIndex(
  { organization_id: 1, subject: 1, predicate: 1, status: 1 },
  { name: "idx_org_subject_predicate_status" }
);

db.fact_refs.createIndex(
  { organization_id: 1, run_id: 1, chunk_id: 1 },
  { name: "idx_org_fact_refs_run_chunk" }
);

db.review_signals.createIndex(
  { organization_id: 1, source_id: 1, kind: 1 },
  { name: "idx_org_signals_source_kind" }
);

// 2. Model versioning & human control collections
db.model_versions.createIndex(
  { organization_id: 1, version: 1 },
  { unique: true, name: "uniq_org_model_version" }
);

db.decisions.createIndex(
  { organization_id: 1, subject_id: 1, created_at: -1 },
  { name: "idx_org_decision_subject" }
);

db.conflicts.createIndex(
  { organization_id: 1, status: 1 },
  { name: "idx_org_conflict_status" }
);

db.events.createIndex(
  { organization_id: 1, run_id: 1, created_at: 1 },
  { name: "idx_org_events_run_created" }
);

db.agent_specs.createIndex(
  { organization_id: 1, status: 1 },
  { name: "idx_org_agent_specs_status" }
);

db.acknowledgements.createIndex(
  { organization_id: 1, decision_id: 1, agent_id: 1 },
  { unique: true, name: "uniq_org_decision_agent_ack" }
);

// 3. Step 4 / Step 5 demo CRM intervention & labeled simulation collections
db.simulation_runs.createIndex(
  { organization_id: 1, arm: 1, seed: 1 },
  { name: "idx_org_sim_arm_seed" }
);

db.simulation_events.createIndex(
  { organization_id: 1, simulation_run_id: 1, period: 1, actor_type: 1 },
  { name: "idx_org_sim_run_period_actor" }
);

db.crm_deals_demo.createIndex(
  { organization_id: 1, deal_id: 1, crm_schema_version: 1 },
  { unique: true, name: "uniq_org_demo_deal_schema" }
);
