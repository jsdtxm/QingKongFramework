https://martinheinz.dev/blog/105

```
-- Create a schedule to run the procedure every hour
SELECT cron.schedule('0 * * * *', $$CALL expire_rows('1 hour');$$);

-- List all scheduled jobs
SELECT * FROM cron.job;
```