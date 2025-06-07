from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import process_due_auctions

def start():
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.add_job(process_due_auctions, 'interval', minutes=30)
    scheduler.start()