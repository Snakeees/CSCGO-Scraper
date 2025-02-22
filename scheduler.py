import sched
import time

from scraper import run

scheduler = sched.scheduler(time.time, time.sleep)


def scheduled_run(interval):
    """Schedule the run function to execute at a regular interval."""
    print(run())
    scheduler.enter(interval, 1, scheduled_run, (interval,))


if __name__ == "__main__":
    INTERVAL = 60
    scheduler.enter(0, 1, scheduled_run, (INTERVAL,))
    scheduler.run()
