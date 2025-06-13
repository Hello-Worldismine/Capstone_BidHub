# app/apps.py
from django.apps import AppConfig
import os
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

class AuctionAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # RUN_MAIN 이 'true'인 실제 서버 프로세스에서만 스케줄러 실행
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from app.tasks import process_due_auctions

        scheduler = BackgroundScheduler(timezone='Asia/Seoul')
        scheduler.add_job(
            process_due_auctions,
            'cron',
            minute='*/5',
            id='process_due_auctions',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
