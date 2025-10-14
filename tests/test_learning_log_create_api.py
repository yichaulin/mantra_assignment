import pytest
import uuid
from datetime import timezone
from django.urls import reverse
from learning_log.models import Record
from django.utils.dateparse import parse_datetime


# 標示這些測試需要 DB（pytest-django 會自動用交易隔離）
pytestmark = pytest.mark.django_db
URL = reverse("post-learning-log")
TEST_USER_ID = uuid.uuid4()
HEADERS = {
    "HTTP_X_USER_ID": TEST_USER_ID
}
BASE_PAYLOAD = {
    "study_timestamp": "2025-10-12T15:10:00+09:00",
    "word_count": 11,
    "study_time": 123,
    "idempotency_key": uuid.uuid4()
}

def test_create_record(api_client):
    payload = BASE_PAYLOAD.copy()
    res = api_client.post(URL, payload, format="json", **HEADERS)
    assert res.status_code == 201

    obj = Record.objects.filter(
            user_id=TEST_USER_ID,
            idempotency_key=payload["idempotency_key"],
    ).first()

    assert obj is not None
    assert obj.word_count == payload["word_count"]
    assert (
        obj.study_timestamp.astimezone(timezone.utc)
        == parse_datetime(payload["study_timestamp"]).astimezone(timezone.utc)
    )
    assert obj.study_time == payload["study_time"]

def test_create_with_study_timestamp_without_timezone(api_client):
    payload = BASE_PAYLOAD.copy()
    payload["study_timestamp"] = "2025-10-09T17:10:00"
    api_client.post(URL, payload, format="json", **HEADERS)

    obj = Record.objects.filter(
            user_id=TEST_USER_ID,
            idempotency_key=payload["idempotency_key"],
    ).first()
    assert (
        obj.study_timestamp.astimezone(timezone.utc)
        == parse_datetime(payload["study_timestamp"]).astimezone(timezone.utc)
    )

def test_duplicated_request(api_client):
    payload = BASE_PAYLOAD.copy()

    res = api_client.post(URL, payload, format="json", **HEADERS)
    assert res.status_code == 201

    # duplicated request with the same idempotency_key
    duplicated_req_payload = {**payload, "word_count": 99} 
    res = api_client.post(URL, duplicated_req_payload, format="json", **HEADERS)
    assert res.status_code == 201

    records = list(Record.objects.filter(
            user_id=TEST_USER_ID,
            idempotency_key=payload["idempotency_key"],
    ))
    assert len(records) == 1

    ## ensure the persisted record is from first request
    records[0].word_count == payload["word_count"]


# def test_retrieve_post(api_client, post_factory):
#     post = post_factory(title="Detail")
#     url = f"/api/posts/{post.id}/"
#     res = api_client.get(url)
#     assert res.status_code == 200
#     assert res.json()["title"] == "Detail"

# def test_update_post(api_client, post_factory):
#     post = post_factory(title="Old")
#     url = f"/api/posts/{post.id}/"
#     res = api_client.patch(url, {"title": "New"}, format="json")
#     assert res.status_code == 200
#     assert res.json()["title"] == "New"

# def test_delete_post(api_client, post_factory):
#     post = post_factory()
#     url = f"/api/posts/{post.id}/"
#     res = api_client.delete(url)
#     assert res.status_code == 204
#     # 再打一次應該 404
#     res2 = api_client.get(url)
#     assert res2.status_code == 404