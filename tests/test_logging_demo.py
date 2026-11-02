import logging

from examples.logging_demo import run_demo


def test_run_demo_logs_info_and_warning(caplog):
    caplog.set_level(logging.INFO, logger="operations_demo")
    run_demo()
    assert caplog.record_tuples == [
        (
            "operations_demo",
            logging.INFO,
            "Demo started",
        ),
        (
            "operations_demo",
            logging.WARNING,
            "Demo warning: processing continues",
        ),
    ]
