# Daily Aggregator

## Requirements
- Python: v3.13+
- PostgreSQL: v14+

## How To Run
### Initial Setup
```bash
uv sync --all-groups
uv run manage.py migrate
```

### Run Test
```bash
uv run poe test
```

### Run Server
```bash
uv run manage.py runserver
```


## Implementation Explainations
### Table schema (learning_log_record)
Columns:
- **user_id(UUID)**: Unique identifier for the user
- **word_count(Integer)**: Number of words studied
- **study_time(Integer)**: Total study time in seconds
- **study_timestamp(Timestamp)**: Time when the study activity occurred
- **idempotency_key(UUID)**: Unique key to prevent duplicate requests
- **created_at(Timestamp)**: Record creation timestamp


Uniqe Constraint:
- (user_id, idempotency_key)

Index:
- (user_id, study_timestamp)

### API: Create a new learning recrod
- Authentication is skipped in this MVP stage; user_id is passed via request headers.
- Since this endpoint is for record creation, it simply returns HTTP 201 (Created) with no content.
- To prevent duplicate submissions, the request includes an idempotency_key.
    - If a record with the same `idempotency_key` already exists, the request is silently ignored (no error returned).

### API: Summary user's learning records
- Aggregating user records is computationally expensive, so data is queried and summarized directly in raw SQL for performance.
- Query parameters such as ISO8601 timestamps and `granularity` enums are validated before execution.
- The API extracts the timezone offset from the `from` timestamp and applies it consistently across SQL queries and response timestamps.
- The `from` timestamp’s timezone takes precedence if `to` includes a different offset.

### SQL script (user_summary.sql)
**1. What is `tz_revert_offset`?**
`tz_revert_offset` represents the timezone offset with the opposite sign.
For example:
`+09:00` → `-09:00`

**2. Why does it need the `tz_revert_offset`?**
PostgreSQL handles `AT TIME ZONE` differently depending on whether you pass a timezone name or a numeric offset.
```sql
-- Using a timezone name (expected behavior)
SELECT '2025-10-15T00:00:00+09:00'::timestamptz AT TIME ZONE 'Asia/Tokyo';
-- → 2025-10-15 00:00:00  ✅

-- Using a timezone offset (unexpected conversion)
SELECT '2025-10-15T00:00:00+09:00'::timestamptz AT TIME ZONE '+09:00';
-- → 2025-10-14 06:00:00  ❌
```

Because the API only receives timezone offsets, not names, direct conversion can lead to incorrect results during `date_trunc()` aggregation.
To fix this, we apply the reversed offset:
```sql
SELECT '2025-10-15T00:00:00+09:00'::timestamptz AT TIME ZONE '-09:00';
-- → 2025-10-15 00:00:00 ✅
```


**3. Why does it need to handle timezone again in `date_tunc` function?**
By default, Django stores timestamps as `timestamptz`, which can cause confusion when the PostgreSQL server timezone differs from the intended one.
If not handled, truncating timestamps may produce unexpected results.
```sql
SET TIMEZONE = 'UTC';
SELECT date_trunc('day', '2025-10-12 00:00:01+09:00'::timestamptz);
-- Expected: 2025-10-12 00:00:00+09:00
-- Actual:   2025-10-11 00:00:00+00:00 ❌
```

To ensure consistency, convert to the desired timezone before truncation:
```sql
SET TIMEZONE = 'UTC';
SELECT date_trunc('day', '2025-10-12 00:00:01+09:00'::timestamptz AT TIME ZONE 'Asia/Tokyo');
-- → 2025-10-12 00:00:00 ✅
```
This approach ensures all aggregation results align with the user’s expected local time.

## Future Improvements
- Implement JWT-based authentication.
- Make the SMA (Simple Moving Average) window size configurable via environment variables, or automatically adjust based on granularity.
- If the volume of persisted learning records becomes large, consider precomputing the `date_trunc` value of hour/day/month at record creation time to reduce the aggregation workload and improve query performance.