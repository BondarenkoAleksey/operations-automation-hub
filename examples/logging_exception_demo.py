import logging

logger = logging.getLogger("operations_exception_demo")


def run_exception_demo() -> None:
    try:
        int("not-a-number")
    except ValueError:
        logger.exception("Demo processing failed")
    logger.info("Demo continues after handled error")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )
    run_exception_demo()
