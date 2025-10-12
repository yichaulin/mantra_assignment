from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RecordSerializer
from django.db import IntegrityError, transaction, connection
from pathlib import Path
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta, timezone

class RecordCreateView(APIView):
    def post(self, request):
        user_id = request.headers.get("X-USER-ID")

        data = request.data.copy()
        data["user_id"] = user_id

        record = RecordSerializer(data=data)
        record.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                record.save()
        except IntegrityError:
            return Response(status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_201_CREATED)

class UserSummaryView(APIView):
    def get(self, request, user_id):
        params = request.GET

        from_timestamp = params.get("from")
        to_timestamp = params.get("to")
        granularity = params.get("granularity")

        # TODO: load from ENV or based on granularity
        window_size = 3

        if not from_timestamp or not to_timestamp:
            return Response({"error": "'from' and 'to' are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from_ts, tz_offset, tz_revert_offset = parse_iso8601_with_offset_and_revert_offset(from_timestamp)
        except ValueError as e:
            return Response({"error": "'from' is not iso8601 format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            to_ts, _, _ = parse_iso8601_with_offset_and_revert_offset(to_timestamp)
        except ValueError as e:
            return Response({"error": "'to' is not iso8601 format"}, status=status.HTTP_400_BAD_REQUEST)

        if granularity not in ("hour", "day", "month"):
            return Response({"error": "invalid granularity"}, status=status.HTTP_400_BAD_REQUEST)

        sql_file = Path(__file__).resolve().parent / "sql/user_summary.sql"
        sql = sql_file.read_text(encoding="utf-8")
        query_params = {
            "user_id": user_id,
            "from_ts": from_ts,
            "to_ts": to_ts,
            "granularity": granularity,
            "window_size": window_size,
            "tz_revert_offset": tz_revert_offset,
        }

        with connection.cursor() as cur:
            cur.execute(sql, query_params)
            rows = cur.fetchall()

        summaries = [
            {
                "timestamp": attach_timezone(row[0], tz_offset),
                "words_sma": row[3],
                "time_sma": row[4],
            } for row in rows
        ]

        return Response({"summaries": summaries}, status=status.HTTP_200_OK)

def parse_iso8601_with_offset_and_revert_offset(s: str):
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    dt = datetime.fromisoformat(s)

    offset = dt.utcoffset()
    sign = '+' if offset >= timedelta(0) else '-'
    revert_sign = '-' if offset >= timedelta(0) else '+'
    total_minutes = abs(int(offset.total_seconds() // 60))
    hh, mm = divmod(total_minutes, 60)
    offset_str = f"{sign}{hh:02d}:{mm:02d}"
    revert_offset_str = f"{revert_sign}{hh:02d}:{mm:02d}"

    return dt, offset_str, revert_offset_str

def attach_timezone(dt: datetime, offset_str: str):
    sign = 1 if offset_str[0] == '+' else -1
    hours, minutes = map(int, offset_str[1:].split(':'))
    offset = timedelta(hours=hours, minutes=minutes) * sign
    tz = timezone(offset)

    return dt.replace(tzinfo=tz)


