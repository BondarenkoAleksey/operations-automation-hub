import logging

from examples.logging_exception_demo import run_exception_demo


def test_run_exception_demo_logs_error_and_continues(caplog):
    caplog.set_level(logging.INFO, logger="operations_exception_demo")
    run_exception_demo()
    assert caplog.record_tuples == [
        (
            "operations_exception_demo",
            logging.ERROR,
            "Demo processing failed",
        ),
        (
            "operations_exception_demo",
            logging.INFO,
            "Demo continues after handled error",
        ),
    ]
    error_record = caplog.records[0]
    assert error_record.exc_info is not None
    assert error_record.exc_info[0] is ValueError
    assert error_record.exc_info[2] is not None

    assert caplog.records[1].exc_info is None
