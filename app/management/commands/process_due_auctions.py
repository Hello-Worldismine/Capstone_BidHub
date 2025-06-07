from django.core.management.base import BaseCommand
from app.tasks import process_due_auctions

class Command(BaseCommand):
    help = "30분 간격으로 PutCrypt 후 낙찰처리할 항목 처리"

    def handle(self, *args, **kwargs):
        process_due_auctions()
