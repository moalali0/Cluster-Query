# AWS Scheduler Plan (Future Production)

Timezone: `Europe/London`

- 08:45 Mon-Fri: Start EC2 inference host
- 09:30 Mon-Fri: Trigger ingestion job (S3 -> Postgres)
- 18:00 Mon-Fri: Stop EC2 inference host

This avoids the previous conflict where ingestion started before the instance booted.
