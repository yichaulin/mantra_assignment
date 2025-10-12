WITH series AS (
  SELECT * 
  FROM generate_series(
    date_trunc(%(granularity)s, %(from_ts)s AT TIME ZONE %(tz_revert_offset)s),
    date_trunc(%(granularity)s, %(to_ts)s AT TIME ZONE %(tz_revert_offset)s),
    CASE %(granularity)s
      WHEN 'hour'  THEN INTERVAL '1 hour'
      WHEN 'day'   THEN INTERVAL '1 day'
      WHEN 'month' THEN INTERVAL '1 month'
    END
  ) AS gs(summary_ts)
),
agg AS (
  SELECT
    date_trunc(%(granularity)s, study_timestamp AT TIME ZONE %(tz_revert_offset)s) AS agg_ts,
    SUM(word_count) AS sum_words,
    SUM(study_time) AS sum_time
  FROM learning_log_record
  WHERE user_id = %(user_id)s
    AND study_timestamp >= %(from_ts)s AND study_timestamp <= %(to_ts)s
  GROUP BY 1
),
joined AS (
  SELECT s.summary_ts,
         COALESCE(a.sum_words, 0) AS sum_words,
         COALESCE(a.sum_time,  0) AS sum_time
  FROM series s
  LEFT JOIN agg a ON s.summary_ts = a.agg_ts
),
sma AS (
  SELECT
    joined.summary_ts,
    sum_words,
    sum_time,
    AVG(sum_words) OVER (
      ORDER BY joined.summary_ts
      ROWS BETWEEN %(window_size)s - 1 PRECEDING AND CURRENT ROW
    ) AS words_sma,
    AVG(sum_time) OVER (
      ORDER BY joined.summary_ts
      ROWS BETWEEN %(window_size)s - 1 PRECEDING AND CURRENT ROW
    ) AS time_sma
  FROM joined
)
SELECT
  summary_ts, sum_words, sum_time, round(words_sma, 2), round(time_sma, 2)
FROM sma
ORDER BY 1;
