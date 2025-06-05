###########################################################
#Created this from tinkering with Gemini                 #
#This measures the CPU and Memory performance overtime   #
#This is as is                                           #
#TO DO: Refine                                           #
###########################################################

import psutil
import time
import logging
from datetime import datetime

# --- Configuration ---
LOG_FILE = 'system_performance.log'  # Name of the log file
LOG_LEVEL = logging.INFO             # Logging level (e.g., INFO, DEBUG)
# Log message format: timestamp - log level - message
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
# Date format for timestamps in the log
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
# Interval in seconds between each performance check
POLL_INTERVAL_SECONDS = 5
# CPU usage interval for psutil.cpu_percent().
# A value of 1 means it will compare CPU times over 1 second.
# A value of None makes it non-blocking and compares since the last call.
CPU_INTERVAL = 1

# --- Logger Setup ---
def setup_logger():
    """
    Configures the logger to write performance data to a file.
    """
    # Create a logger instance
    logger = logging.getLogger('SystemMonitor')
    logger.setLevel(LOG_LEVEL)

    # Create a file handler to write logs to a file
    # 'a' mode appends to the file if it exists, creates it otherwise
    file_handler = logging.FileHandler(LOG_FILE, mode='a')
    file_handler.setLevel(LOG_LEVEL)

    # Create a formatter to define the log message structure
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    # This ensures logs from this logger instance go to the file
    if not logger.handlers: # Avoid adding multiple handlers if re-running in an interactive session
        logger.addHandler(file_handler)

    return logger

# --- Performance Metrics Functions ---
def get_cpu_usage():
    """
    Retrieves the current system-wide CPU utilization percentage.
    """
    # psutil.cpu_percent(interval) returns the CPU usage percentage.
    # The 'interval' parameter specifies the time to wait for the second measurement.
    # If interval is 0.0 or None, it returns a non-blocking instantaneous CPU usage
    # (percentage since the last call or module import).
    # For more accurate readings over time, a small interval is recommended.
    cpu_percent = psutil.cpu_percent(interval=CPU_INTERVAL)
    return cpu_percent

def get_memory_usage():
    """
    Retrieves current system memory usage statistics.
    Returns a dictionary with total, available, used memory (in GB), and percentage used.
    """
    virtual_mem = psutil.virtual_memory()
    memory_info = {
        'total_gb': round(virtual_mem.total / (1024**3), 2),      # Convert bytes to GB
        'available_gb': round(virtual_mem.available / (1024**3), 2), # Convert bytes to GB
        'used_gb': round(virtual_mem.used / (1024**3), 2),        # Convert bytes to GB
        'percent_used': virtual_mem.percent
    }
    return memory_info

# --- Main Monitoring Loop ---
def monitor_system(logger):
    """
    Continuously monitors and logs CPU and memory usage.
    """
    logger.info("System performance monitoring started.")
    print(f"Monitoring system performance. Logging to '{LOG_FILE}'. Press Ctrl+C to stop.")

    try:
        while True:
            # Get current CPU usage
            cpu_usage_percent = get_cpu_usage()

            # Get current memory usage
            memory_usage_info = get_memory_usage()

            # Format the log message
            log_message = (
                f"CPU Usage: {cpu_usage_percent:.2f}% | "
                f"Memory: {memory_usage_info['percent_used']}% used "
                f"({memory_usage_info['used_gb']}GB / {memory_usage_info['total_gb']}GB total)"
            )

            # Log the performance data
            logger.info(log_message)

            # Wait for the defined interval before the next check
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        # Handle user interruption (Ctrl+C)
        logger.info("System performance monitoring stopped by user.")
        print("\nMonitoring stopped.")
    except Exception as e:
        # Log any other exceptions that might occur
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}. Check the log file for details.")

# --- Script Entry Point ---
if __name__ == "__main__":
    # Set up the logger
    performance_logger = setup_logger()
    # Start the monitoring process
    monitor_system(performance_logger)