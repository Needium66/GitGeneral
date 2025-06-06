#######################################################################################################
#Leverage Gemini to generate a monthly log cleanup on a server using Python                           #
#Prompted it to Check and Improve the Code based on Reflection Agentic pattern                        #
#TO DO: Leverage a Multi-Agent Framework to autonomously do all the work, instead of me triggering it #
#######################################################################################################


#######################################
# Python Code for the Monthly reminder
#######################################


import os
import datetime

def clean_server_logs():
    """
    Deletes log files in the specified directory that are older than 30 days.
    """
    # --- Configuration ---
    # ⚠️ IMPORTANT: Change this to your server's log directory.
    log_directory = "/var/log/myapp/"
    days_to_keep = 30
    # --- End of Configuration ---

    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=days_to_keep)

    if not os.path.exists(log_directory):
        print(f"Error: Log directory not found at '{log_directory}'")
        return

    print(f"Scanning {log_directory} for logs older than {days_to_keep} days...")

    for filename in os.listdir(log_directory):
        file_path = os.path.join(log_directory, filename)
        
        # Ensure it's a file before trying to get its modification time
        if os.path.isfile(file_path):
            try:
                file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mod_time < cutoff:
                    print(f"Deleting old log file: {filename}")
                    os.remove(file_path)
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    print("Log cleaning process complete.")

if __name__ == "__main__":
    clean_server_logs()


#################################
# Refactored Version
################################

import os
import datetime
import argparse
import logging

# --- Setup robust logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    # Uncomment the line below to log to a file instead of the console
    # filename='log_cleanup.log'
)

def clean_server_logs(log_directory: str, days_to_keep: int) -> None:
    """
    Scans a directory and deletes files older than a specified number of days.

    Args:
        log_directory (str): The absolute path to the directory containing logs.
        days_to_keep (int): The maximum age of files (in days) to keep.
    """
    if not os.path.isdir(log_directory):
        logging.error(f"Error: Log directory not found or is not a directory at '{log_directory}'")
        return

    logging.info(f"Scanning '{log_directory}' for files older than {days_to_keep} days...")

    now = datetime.datetime.now()
    cutoff_date = now - datetime.timedelta(days=days_to_keep)
    file_count = 0
    deleted_count = 0

    try:
        # Use os.scandir() for better efficiency
        with os.scandir(log_directory) as entries:
            for entry in entries:
                file_count += 1
                # Check if it's a file (and not a symlink to a dir, etc.)
                if entry.is_file():
                    try:
                        # entry.stat().st_mtime is the modification time
                        mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                        if mod_time < cutoff_date:
                            logging.info(f"Deleting old log file: {entry.name}")
                            os.remove(entry.path)
                            deleted_count += 1
                    except FileNotFoundError:
                        # This can happen if the file is deleted by another process
                        # between the scandir() call and the os.remove() call.
                        logging.warning(f"Could not find file '{entry.name}' for deletion, it may have been removed already.")
                    except Exception as e:
                        logging.error(f"Error processing file '{entry.name}': {e}")
    except Exception as e:
        logging.error(f"Failed to scan directory '{log_directory}': {e}")


    logging.info(f"Scan complete. Found {file_count} items and deleted {deleted_count} old files.")

if __name__ == "__main__":
    # --- Setup command-line argument parsing ---
    parser = argparse.ArgumentParser(
        description="Clean up old log files in a specified directory."
    )
    parser.add_argument(
        "-d", "--directory",
        type=str,
        required=True,
        help="The log directory to clean."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Delete files older than this many days (default: 30)."
    )

    args = parser.parse_args()

    # --- Run the main function ---
    clean_server_logs(log_directory=args.directory, days_to_keep=args.days)