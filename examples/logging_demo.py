import logging

logger = logging.getLogger("operations_demo")


def run_demo() -> None:
    logger.debug("Preparing demo")
    logger.info("Demo started")
    logger.warning("Demo warning: processing continues")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )
    run_demo()
