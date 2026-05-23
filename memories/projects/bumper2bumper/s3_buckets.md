---
name: SplitLedger doesn't use an S3 bucket for app data
description: Attachments go through Serverpod's session.storage (storageId=public), which falls back to DatabaseCloudStorage because no S3 cloud-storage backend is configured in any env yaml.
type: project
originSessionId: fe5ad88f-5dda-447c-b73a-812c0e81c5ed
---
The only actual S3 reference in the repo is `splitledger-terraform` at `infrastructure/aws/main.tf:12` — that's the Terraform **backend state** bucket, not app data. `splitledger-deploy` appears in `infrastructure/aws/project.env` but isn't referenced in any code.

Attachments (`backend/splitledger_server/lib/src/endpoints/attachment_endpoint.dart:67`) use `session.storage.storeFile(storageId: 'public', ...)` — Serverpod's storage abstraction. No S3 cloud-storage backend is configured in `backend/splitledger_server/config/{development,test,staging,production}.yaml`, so Serverpod falls back to `DatabaseCloudStorage` — files land in the `serverpod_cloud_storage` Postgres table, and `transaction_attachments.s3Path` is the storage key (not an S3 URL, despite the field name).

**Why:** User correction after I built an S3-browsing pane and listed terraform-state buckets as if they were app-owned. They're not.

**How to apply:** When surfacing storage in tooling, query the `transaction_attachments` table (or Serverpod's storage API) rather than S3. If/when an S3 backend gets wired up, the relevant signal is a `cloudStorage` section appearing in one of the config yamls — detect that, don't assume from `project.env` or Terraform variables. Don't infer resource ownership from config string names alone.
