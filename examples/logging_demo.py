import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)


logger = logging.getLogger("operations_demo")

logger.debug("Preparing demo")
logger.info("Demo started")
logger.warning("Demo warning: processing continues")
