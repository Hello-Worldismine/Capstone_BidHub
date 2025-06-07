from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

class AuctionAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        from app.tasks import process_due_auctions  # ← 여기로 옮겨야 안전

        scheduler = BackgroundScheduler(timezone='Asia/Seoul')
        scheduler.add_job(
            process_due_auctions,
            'cron',
            minute='0,30',  # 매시 정각과 30분
            id='process_due_auctions',
            replace_existing=True
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
