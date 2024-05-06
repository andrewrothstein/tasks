from dotenv import load_dotenv
import logging
import os

import logging
import sys

def setup_logging():
    # Create a stream handler that writes to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)

    # Configure the formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)

    # Get the root logger and add the handler to it
    root_logger = logging.getLogger()
    root_logger.addHandler(stdout_handler)

    # Set the logging level for the root logger
    root_logger.setLevel(logging.INFO)

def main() :
    setup_logging()
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("resolved CLIENT_SECRET='%s'", os.getenv("CLIENT_SECRET"))

if __name__ == '__main__':
    main()
