import logging

import pytest

from examples.logging_demo import run_demo


@pytest.mark.parametrize(
    ("threshold", "expected_records"),
    [
        (
            logging.DEBUG,
            [
                (
                    "operations_demo",
                    logging.DEBUG,
                    "Preparing demo",
                ),
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
            ],
        ),
        (
            logging.INFO,
            [
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
            ],
        ),
        (
            logging.WARNING,
            [
                (
                    "operations_demo",
                    logging.WARNING,
                    "Demo warning: processing continues",
                ),
            ],
        ),
    ],
    ids=["debug", "info", "warning"],
)
def test_run_demo_respects_logging_threshold(caplog, threshold, expected_records):
    caplog.set_level(threshold, logger="operations_demo")
    run_demo()
    assert caplog.record_tuples == expected_records
