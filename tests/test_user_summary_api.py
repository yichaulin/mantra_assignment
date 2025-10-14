import pytest
import uuid
from datetime import timezone
from django.urls import reverse
from learning_log.models import Record
from django.utils.dateparse import parse_datetime
from statistics import mean


# 標示這些測試需要 DB（pytest-django 會自動用交易隔離）
pytestmark = pytest.mark.django_db
TEST_USER_ID = uuid.uuid4()
URL = reverse("user-summary", kwargs={"user_id": TEST_USER_ID})

def test_summeries_with_hourly(api_client, learning_log_factory):
    records = [{
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 4,
        "study_time": 9,
        "study_timestamp": "2025-10-12T01:00:01+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 6,
        "study_time": 11,
        "study_timestamp": "2025-10-12T01:23:59+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 20,
        "study_time": 30,
        "study_timestamp": "2025-10-12T02:01:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 30,
        "study_time": 40,
        "study_timestamp": "2025-10-12T03:01:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 40,
        "study_time": 50,
        "study_timestamp": "2025-10-12T04:01:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 50,
        "study_time": 60,
        "study_timestamp": "2025-10-12T05:00:00+09:00" 
    }]

    for r in records:
        learning_log_factory(**r)

    res = api_client.get(URL, data={
        "from": "2025-10-12T01:00:00+09:00",
        "to": "2025-10-12T05:00:00+09:00",
        "granularity": "hour",
    })
    assert res.status_code == 200

    summaries = res.json()["summaries"]
    assert len(summaries) == 5

    assert summaries[0] == {
        "timestamp": "2025-10-12T01:00:00+09:00",
        "words_sma": 10.0, # (4 + 6) / 1
        "time_sma": 20.0, # (9 + 11) / 1
    }
    assert summaries[1] == {
        "timestamp": "2025-10-12T02:00:00+09:00",
        "words_sma": 15.0, # ((4 + 6) + 20) / 2,
        "time_sma": 25.0, # ((9 + 11) + 30) / 2
    }
    assert summaries[2] == {
        "timestamp": "2025-10-12T03:00:00+09:00",
        "words_sma": 20.0, # ((4 + 6) + 20 + 30) / 3,
        "time_sma": 30.0, # ((9 + 11) + 30 + 40) / 3
    }
    assert summaries[3] == {
        "timestamp": "2025-10-12T04:00:00+09:00",
        "words_sma": 30.0, # (20 + 30 + 40) / 3,
        "time_sma": 40.0, # (30 + 40 + 50) / 3
    }
    assert summaries[4] == {
        "timestamp": "2025-10-12T05:00:00+09:00",
        "words_sma": 40.0, # (30 + 40 + 50) / 3,
        "time_sma": 50.0, # (40 + 50 + 60) / 3
    }


def test_summeries_with_daily(api_client, learning_log_factory):
    records = [{
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 4,
        "study_time": 9,
        "study_timestamp": "2025-10-12T00:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 6,
        "study_time": 11,
        "study_timestamp": "2025-10-12T23:59:59+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 20,
        "study_time": 30,
        "study_timestamp": "2025-10-13T01:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 30,
        "study_time": 40,
        "study_timestamp": "2025-10-14T02:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 40,
        "study_time": 50,
        "study_timestamp": "2025-10-15T03:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 50,
        "study_time": 60,
        "study_timestamp": "2025-10-16T00:00:00+09:00" 
    }]

    for r in records:
        learning_log_factory(**r)

    res = api_client.get(URL, data={
        "from": "2025-10-12T00:00:00+09:00",
        "to": "2025-10-15T23:59:59+09:00",
        "granularity": "day",
    })
    assert res.status_code == 200

    summaries = res.json()["summaries"]
    assert len(summaries) == 4

    assert summaries[0] == {
        "timestamp": "2025-10-12T00:00:00+09:00",
        "words_sma": 10.0, # (4 + 6) / 1
        "time_sma": 20.0, # (9 + 11) / 1
    }
    assert summaries[1] == {
        "timestamp": "2025-10-13T00:00:00+09:00",
        "words_sma": 15.0, # ((4 + 6) + 20) / 2,
        "time_sma": 25.0, # ((9 + 11) + 30) / 2
    }
    assert summaries[2] == {
        "timestamp": "2025-10-14T00:00:00+09:00",
        "words_sma": 20.0, # ((4 + 6) + 20 + 30) / 3,
        "time_sma": 30.0, # ((9 + 11) + 30 + 40) / 3
    }
    assert summaries[3] == {
        "timestamp": "2025-10-15T00:00:00+09:00",
        "words_sma": 30.0, # (20 + 30 + 40) / 3,
        "time_sma": 40.0, # (30 + 40 + 50) / 3
    }


def test_summeries_with_monthly(api_client, learning_log_factory):
    records = [{
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 4,
        "study_time": 9,
        "study_timestamp": "2025-03-12T00:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 6,
        "study_time": 11,
        "study_timestamp": "2025-03-13T00:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 20,
        "study_time": 30,
        "study_timestamp": "2025-04-14T01:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 30,
        "study_time": 40,
        "study_timestamp": "2025-05-15T02:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 40,
        "study_time": 50,
        "study_timestamp": "2025-06-16T03:00:00+09:00" 
    }, {
        "idempotency_key": uuid.uuid4(),
        "user_id": TEST_USER_ID,
        "word_count": 50,
        "study_time": 60,
        "study_timestamp": "2025-07-17T00:00:00+09:00" 
    }]

    for r in records:
        learning_log_factory(**r)

    res = api_client.get(URL, data={
        "from": "2025-03-12T00:00:00+09:00",
        "to": "2025-07-16T23:59:59+09:00",
        "granularity": "month",
    })
    assert res.status_code == 200

    summaries = res.json()["summaries"]
    assert len(summaries) == 5

    assert summaries[0] == {
        "timestamp": "2025-03-01T00:00:00+09:00",
        "words_sma": 10.0, # (4 + 6) / 1
        "time_sma": 20.0, # (9 + 11) / 1
    }
    assert summaries[1] == {
        "timestamp": "2025-04-01T00:00:00+09:00",
        "words_sma": 15.0, # ((4 + 6) + 20) / 2,
        "time_sma": 25.0, # ((9 + 11) + 30) / 2
    }
    assert summaries[2] == {
        "timestamp": "2025-05-01T00:00:00+09:00",
        "words_sma": 20.0, # ((4 + 6) + 20 + 30) / 3,
        "time_sma": 30.0, # ((9 + 11) + 30 + 40) / 3
    }
    assert summaries[3] == {
        "timestamp": "2025-06-01T00:00:00+09:00",
        "words_sma": 30.0, # (20 + 30 + 40) / 3,
        "time_sma": 40.0, # (30 + 40 + 50) / 3
    }
    assert summaries[4] == {
        "timestamp": "2025-07-01T00:00:00+09:00",
        "words_sma": 23.33, # (30 + 40) / 3,
        "time_sma": 30.0, # (40 + 50) / 3
    }
