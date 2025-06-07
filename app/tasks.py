# app/tasks.py
import requests
from django.utils import timezone
from django.db.models import Max
from app.models import AuctionItem, AuctionSchedule

GRAPHQL_URL = "https://api.studio.thegraph.com/query/111711/capstone/version/latest"

def has_event(trade_num: int, event_name: str) -> bool:
    query = f"""
    {{
      {event_name.lower()}s(where: {{tradeNum: "{trade_num}"}}) {{
        id
      }}
    }}
    """
    response = requests.post(GRAPHQL_URL, json={'query': query})
    data = response.json()
    return bool(data['data'][f'{event_name.lower()}s'])

def process_due_auctions():
    now = timezone.now()

    # 매각결정기일이 지나간 항목들 중 가장 최근 회차
    latest_schedules = (
        AuctionSchedule.objects.filter(schedule_type="매각결정기일", decision_date__lt=now)
        .values('auction_item_id')
        .annotate(latest_date=Max('decision_date'))
    )

    for entry in latest_schedules:
        item_id = entry['auction_item_id']
        latest_decision_date = entry['latest_date']

        try:
            schedule = AuctionSchedule.objects.get(
                auction_item_id=item_id,
                schedule_type="매각결정기일",
                decision_date=latest_decision_date
            )
            item = AuctionItem.objects.get(id=item_id)
            trade_num = int(item.case_number.replace("타경", ""))

            has_put = has_event(trade_num, "PutCrypt")
            has_win = has_event(trade_num, "BidWin")

            if has_put and not has_win:
                # decode & input 
                res = requests.post(
                    "http://localhost:8000/api/decode_and_input_decrypt/",
                    json={
                        "trade_num": trade_num,
                        "due_date": int(latest_decision_date.timestamp())
                    }
                )
                print(f"{trade_num} decode 처리 완료: {res.json()}")

            elif not has_put and not has_win:
                # 유찰 처리
                new_failures = item.auction_failures + 1
                base_price = item.valuation_amount
                if new_failures == 1:
                    new_price = int(base_price * 0.8)
                else:
                    new_price = int(base_price * 0.7)

                item.auction_failures = new_failures
                item.save()

                round_number = schedule.round_number + 1
                
                base_time = latest_decision_date + timezone.timedelta(minutes=30)
                AuctionSchedule.objects.create(
                    auction_item=item,
                    round_number=round_number,
                    auction_date=base_time,
                    schedule_type="매각기일",
                    minimum_price=new_price
                    )
                AuctionSchedule.objects.create(
                    auction_item=item,
                    round_number=round_number,
                    decision_date=base_time,
                    schedule_type="매각결정기일",
                    minimum_price=0
                    )

                print(f"{trade_num} 유찰 처리 완료 (회차 {round_number})")

        except Exception as e:
            print(f"[에러] {item_id} 처리 중 오류 발생: {e}")
