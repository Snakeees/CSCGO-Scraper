import sched
import time
import datetime
from typing import Dict, Any

from scraper import scrape_location
from database import Location, Room, Machine

scheduler = sched.scheduler(time.time, time.sleep)
LOCATION_ID = "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"


def scheduled_scrape(interval: int) -> None:
    """
    Schedule the run function to execute at a regular interval.
    
    Args:
        interval: Time in seconds between runs
    """
    try:
        location_data, rooms, machines = scrape_location(LOCATION_ID)
        Location.upsert(location_data)
        for room in rooms:
            Room.upsert(room)
        for machine in machines:
            Machine.upsert(machine)
    except Exception as e:
        print(f"Error: {e}")

    scheduler.enter(interval, 1, scheduled_scrape, (interval,))


if __name__ == "__main__":
    INTERVAL = 60
    scheduler.enter(0, 1, scheduled_scrape, (INTERVAL,))
    scheduler.run()
