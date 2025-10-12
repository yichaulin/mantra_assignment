from django.db import models
from django.utils import timezone
import uuid

# Create your models here.

class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    word_count = models.PositiveBigIntegerField()
    study_time = models.PositiveBigIntegerField()
    study_timestamp = models.DateTimeField(default=timezone.now)
    idempotency_key = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "idempotency_key"],
                name="uniq_user_id_idemkey",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user_id", "study_timestamp"],
                name="llrecord_user_id_study_ts_idx"
            ),
        ]