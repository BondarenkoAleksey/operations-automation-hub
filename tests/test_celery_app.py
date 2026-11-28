from unittest.mock import patch
from uuid import uuid4

import pytest

from operations_automation_hub.celery_app import run_job_decisions_task
from operations_automation_hub.services.request_decision import ScoringStatus


def test_run_job_decisions_task_restores_payload_types():
    job_id = uuid4()
    request_id = uuid4()
    with patch("operations_automation_hub.celery_app.run_job_decisions") as runner:
        run_job_decisions_task.run(job_id=str(job_id),
                                checks_by_request_id={str(request_id): {
                                    "inn_is_valid": True,
                                    "risk_score": 85,
                                    "scoring_status": ScoringStatus.DECLINED.value,
                                }}, )
        runner.assert_called_once()

        args = runner.call_args.kwargs
        assert args["job_id"] == job_id

        checks = args["checks_by_request_id"][request_id]
        assert checks["scoring_status"] is ScoringStatus.DECLINED
        assert checks["inn_is_valid"] is True
        assert checks["risk_score"] == 85


def test_run_job_decisions_task_rejects_invalid_job_id():
    with patch("operations_automation_hub.celery_app.run_job_decisions") as runner:
        with pytest.raises(ValueError):
            run_job_decisions_task.run(job_id="not-a-uuid", checks_by_request_id={})
        runner.assert_not_called()
