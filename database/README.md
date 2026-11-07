# Database and queries

MongoDB is the planned persistence layer. Credits were confirmed during preparation; **no cluster or database has been provisioned for this project**.

- [SCHEMA.md](SCHEMA.md): proposed collection and lifecycle contracts.
- [queries/inspect.mongosh.js](queries/inspect.mongosh.js): read-only inspection templates.
- [indexes.mongosh.js](indexes.mongosh.js): explicit index setup, to review before applying.
- [fixtures/synthetic-sources.json](fixtures/synthetic-sources.json): invented example inputs only.

These are design artifacts, not a migration already applied to Atlas. A local fixture is not an evaluation dataset. Real source logs remain in their original system until a scoped export is authorized.
