"""
ChefBot Entry Point
===================
"""

import logging
import uvicorn
from core.app_factory import create_app
from core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    logger.info("Starting ChefBot server on http://0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)
