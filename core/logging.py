import logging
import sys

def setup_logging(level=logging.INFO):
    """Setup logging for the entire app"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    return logging.getLogger(__name__)

logger = setup_logging()
