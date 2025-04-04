import sched
import time
import logging
import sys
from core.scraper import scrape_location
from core.database import Location, Room, Machine

# Clear any existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Create separate handlers for stdout (INFO and below) and stderr (WARNING and above)
stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)

# Set log levels
stdout_handler.setLevel(logging.INFO)
stderr_handler.setLevel(logging.WARNING)

# Define a common formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Attach formatter to handlers
stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)

# Add handlers to the root logger
logging.basicConfig(level=logging.DEBUG, handlers=[stdout_handler, stderr_handler])

scheduler = sched.scheduler(time.time, time.sleep)
LOCATION_ID = "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"


def scheduled_scrape(interval: int) -> None:
    """
    Schedule the run function to execute at a regular interval.

    Args:
        interval: Time in seconds between runs
    """
    success = True
    try:
        logging.info(f"Starting scrape for location {LOCATION_ID}")

        location_data, rooms, machines = scrape_location(LOCATION_ID)

        # Log summary of scraped data
        logging.info(
            f"Scraped data summary: "
            f"Location: {location_data.get('label', 'Unknown')}, "
            f"Rooms: {len(rooms)}, "
            f"Machines: {len(machines)}"
        )

        # Track updates
        location_updates = 1 if Location.upsert(location_data) else 0

        room_updates = 0
        for room in rooms:
            if Room.upsert(room):
                room_updates += 1

        # Log machine status summary
        available_machines = sum(1 for m in machines if m.get("timeRemaining", 0) == 0)
        logging.info(
            f"Machine status: "
            f"Total: {len(machines)}, "
            f"Available: {available_machines}, "
            f"In Use: {len(machines) - available_machines}"
        )

        machine_updates = 0
        for machine in machines:
            try:
                if Machine.upsert(machine):
                    machine_updates += 1
            except Exception as e:
                success = False
                logging.error(
                    f"Error updating machine {machine.get('licensePlate', 'Unknown')}: {str(e)}"
                )

        if success:
            logging.info("Database update completed successfully")
        else:
            logging.warning("Database update completed with some errors")

        # Log update summary
        logging.info(
            f"Update summary: "
            f"Locations: {location_updates}, "
            f"Rooms: {room_updates}, "
            f"Machines: {machine_updates}"
        )

    except Exception as e:
        logging.error(f"Scraping error: {str(e)}", exc_info=True)

    scheduler.enter(interval, 1, scheduled_scrape, (interval,))


if __name__ == "__main__":
    logging.info("Scraper service starting")
    INTERVAL = 60
    scheduler.enter(0, 1, scheduled_scrape, (INTERVAL,))
    scheduler.run()
