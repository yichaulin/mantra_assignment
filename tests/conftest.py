import pytest
from rest_framework.test import APIClient
from model_bakery import baker

@pytest.fixture
def api_client():
    """像 Rails 的 `type: :request` 時給你 `get/post` 幫手，這裡給 DRF 的 APIClient。"""
    return APIClient()

@pytest.fixture
def learning_log_factory():
    """產生 Post 假資料的工廠；Rails 對照：FactoryBot.define(:post){}。"""
    def make_record(**kwargs):
        return baker.make("learning_log.Record", **kwargs)
    return make_record