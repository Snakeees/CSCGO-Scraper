import sched
import time
import logging
import sys
from scraper import scrape_location
from database import Location, Room, Machine

# Configure logging to console only
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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

        # Update database
        Location.upsert(location_data)
        for room in rooms:
            Room.upsert(room)
        
        # Log machine status summary
        available_machines = sum(1 for m in machines if m.get('timeRemaining', 0) == 0)
        logging.info(
            f"Machine status: "
            f"Total: {len(machines)}, "
            f"Available: {available_machines}, "
            f"In Use: {len(machines) - available_machines}"
        )
        
        for machine in machines:
            try:
                Machine.upsert(machine)
            except Exception as e:
                success = False
                logging.error(f"Error updating machine {machine.get('licensePlate', 'Unknown')}: {str(e)}")

        if success:
            logging.info("Database update completed successfully")
        else:
            logging.warning("Database update completed with some errors")
        
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}", exc_info=True)

    scheduler.enter(interval, 1, scheduled_scrape, (interval,))


if __name__ == "__main__":
    logging.info("Scraper service starting")
    INTERVAL = 60
    scheduler.enter(0, 1, scheduled_scrape, (INTERVAL,))
    scheduler.run()
