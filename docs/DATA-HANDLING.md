# Public data boundary

Use synthetic inputs for the first demo. Real logs may contain personal data, confidential business information, source quotations, tokens and private instructions. Existing redaction in another project is not proof that an export is safe.

Before a real export: identify the authorized dataset and fields, obtain permission for the intended providers and public artifacts, redact secrets and identifiers, retain consent and provenance, and review the resulting artifact. Keep raw exports outside this repository or in ignored `database/private/`.

Provider credit availability does not grant permission to upload client data. API keys, database URIs, personal email addresses, private agent messages and billing screenshots do not belong in public commits.

Public evidence should contain minimal synthetic inputs, versions, reproducible commands, redacted outputs and measurement limits. Check staged content as well as ignore rules before publication.
