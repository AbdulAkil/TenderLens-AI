# Operations

Run one API, one frontend, one PostgreSQL/pgvector instance and one dedicated worker.
The worker schedules hourly ingest/match/candidate-analysis/digest/reminder/change tasks and daily cleanup.
Jobs have persisted dedup keys, attempts, availability, lease and failure state. Claims
use `FOR UPDATE SKIP LOCKED`; expired leases can recover interrupted jobs. Five failed
attempts require operator retry. Async execution has a ten-minute timeout and a
15-minute lease; synchronous matching is bounded but cannot be preempted by asyncio.
Do not scale workers horizontally until concurrency/provider-outbox behavior is load
tested. No Redis, Kafka or Kubernetes is required for the pilot.

## Daily operator checks

- `/health` for process liveness, `/ready` for DB/migration readiness.
- `/admin` for source jobs, failures, digest review, organization plans and usage.
- `docker compose logs --since=24h worker api` for error types and source failures.
- Confirm the most recent ingest/match/digest jobs completed and no review backlog grew.
- Check database disk growth and available space; alert before 80% capacity.
- Verify provider sandbox status and billing webhooks independently.

The application exposes operational state but does not provision an external uptime
monitor or send incident pages. Configure hosting alerts and ownership before activation.

## Ingestion and backfill

```sh
docker compose exec api python -m tenderlens.ingestion.cli --help
docker compose exec api python -m tenderlens.ingestion.cli --query 'publication-date = 20261113 AND buyer-country = BEL' --scope ALL --max-notices 250
docker compose exec api python -m tenderlens.saas.worker --once
```

Use publication-day slices for historical backfill. Regular jobs replay a three-day
window; a truncated batch fails visibly. Increase the configured bound cautiously or
use smaller windows. Same raw payloads do no reprocessing. Cross-publication amendment
links and a full historical reconciliation are outstanding.

## Retention and deletion

Cleanup removes expired sessions, action tokens and rate windows; terminal delivery
records and completed jobs after 90 days. Pending reviews/failures need operator
attention. Public-source snapshots and customer data do not have automatic blanket
deletion. Define retention with counsel before launch. A deletion request immediately
disables organization sessions; operator completion must cancel/settle external
billing, export if requested, erase tenant rows with reviewed cascades, handle shared
users' memberships, schedule backup expiry and record completion without sensitive data.
There is deliberately no destructive public erase endpoint.

## Backup / restore rehearsal

Keep encrypted off-host backups and encryption keys separately, restrict access, and
set a reviewed retention (example operational target: 7 daily and 4 weekly copies).
These targets are proposals, not configured vendor guarantees. Example Linux host:

```sh
mkdir -p backups
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/tenderlens.dump
```

Encrypt and upload using the selected backup system. Do not commit dumps. Check the
exit code and restore into a **separate empty database**, never overwrite production:

```sh
docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" tenderlens_restore_test'
docker compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d tenderlens_restore_test --no-owner' < backups/tenderlens.dump
```

Verify migration head, row counts, tenant access and a dry-run digest on the restored
copy. Test recovery time and acceptable data loss; no restore SLA is claimed yet.
