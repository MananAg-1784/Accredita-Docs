
import logging

# logging levels => 5
# debug info warning error critical

def create_logger():

    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='logs.log',  
        level=logging.DEBUG,
        encoding='utf-8', 
        filemode='w',
        format='[%(asctime)s] | %(levelname)s | %(funcName)s >>> %(message)s',
        datefmt="%B %d, %H:%M:%S",)
    logger.info("Logger configured...")
    print("Logger configured")
    return logger

logger = create_logger()

