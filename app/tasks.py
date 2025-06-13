import os
import json
import requests
import time
from django.utils import timezone
from django.db import connection, close_old_connections, OperationalError, transaction
from django.conf import settings
from filelock import FileLock, Timeout
from django.db.models import Max
from collections import defaultdict
from datetime import timedelta
from app.models import AuctionItem, BidLog, AuctionSchedule

GRAPHQL_URL = "https://api.studio.thegraph.com/query/111711/capstone/version/latest"
LOCK_FILE = os.path.join(settings.BASE_DIR, 'process_due_auctions.lock')
lock = FileLock(LOCK_FILE, timeout=0)

def execute_with_retry(sql, params=None, max_retries=3, sleep=0.05, item_id=None):
    for _ in range(max_retries):
        try:
            with connection.cursor() as c:
                c.execute(sql, params or [])
            return True
        except OperationalError as e:
            if 'locked' in str(e).lower():
                time.sleep(sleep)
                continue
            print(f"[SQL fatal error] item={item_id}: {e}")
            return False
    print(f"[락 반복 실패] item={item_id}, sql skipped")
    return False

def fetch_chain_events(trade_nums):
    if not trade_nums:
        return set(), set()
    
    nums_str = ','.join(str(n) for n in trade_nums)  # <- 리스트를 숫자 나열 문자열로

    query = json.dumps({
        'query': f"""
        {{
          PutSecs(where: {{ tradeNum_in: [{nums_str}] }}) {{ tradeNum }}
          BidWins(where: {{ tradeNum_in: [{nums_str}] }}) {{ tradeNum }}
        }}
        """
    })
    print(query)
    try:
        res = requests.post(GRAPHQL_URL, data=query, headers={'Content-Type': 'application/json'})
        data = res.json().get('data', {})
        put_set = {int(item['tradeNum']) for item in data.get('PutSecs', [])}
        win_set = {int(item['tradeNum']) for item in data.get('BidWins', [])}
        return put_set, win_set
    except Exception as e:
        print(f"[GraphQL 오류]: {e}")
        return set(), set()

def process_due_auctions():
    try:
        with lock:
            close_old_connections()
            now = timezone.now()
            now = now + timedelta(hours=9)

            print(f"[현재 시각 (now)] {now} ({type(now)})")

            latest_schedules = (
                AuctionSchedule.objects
                .filter(schedule_type='매각결정기일', decision_date__lt=now)
                .values('auction_item_id')
                .annotate(latest_decision=Max('decision_date'))
                )
            # 해당 날짜의 결정기일 객체만 가져옴
            schedules = AuctionSchedule.objects.filter(
                schedule_type='매각결정기일',
                decision_date__in=[s['latest_decision'] for s in latest_schedules]
                )

            item_map = {s.auction_item_id: s for s in schedules}
            item_ids = list(item_map.keys())
            items = AuctionItem.objects.in_bulk(item_ids)
            trade_nums = [int(items[i].case_number.case_number.replace('타경', '')) for i in item_ids]

            put_set, win_set = fetch_chain_events(trade_nums)
            bids = BidLog.objects.filter(trade_num__in=trade_nums)
            bids_by_trade = defaultdict(list)
            for b in bids:
                bids_by_trade[b.trade_num].append(b)

            connection.close(); connection.connect()
            connection.autocommit = False

            with transaction.atomic():
                for item_id, schedule in item_map.items():
                    item = items[item_id]
                    decision_date = schedule.decision_date
                    trade_num = int(item.case_number.case_number.replace('타경', ''))

                    put = trade_num in put_set
                    win = trade_num in win_set

                    if win:
                        continue  # 이미 낙찰 완료 → 처리 필요 없음
                    if put:
                        print(f"[체인 업로드] trade_num={trade_num}")
                        success = True
                        for bid in bids_by_trade[trade_num]:
                            try:
                                from blockchain import inputbid
                                inputbid(
                                    trade_num,
                                    bid.bid_amount,
                                    bid.bid_security,
                                    bid.bidder_address,
                                    int(bid.bid_time.timestamp())
                                    )
                            except Exception as e:
                                print(f"[inputBid 실패] {e}")
                                success = False
                                break
                        if success:
                            from blockchain import confirm_bid
                            due_ts = int((decision_date + timezone.timedelta(hours=1)).timestamp())
                            confirm_bid(trade_num, due_ts)
                            print("confirmbid")


                    else:
                        print(f"[유찰 처리] trade_num={trade_num}")

                        delete_sql = (
                            "DELETE FROM auction_schedule "
                            "WHERE id = %s"
                            )
                        execute_with_retry(delete_sql, [schedule.id], item_id=item_id)


                        new_fail = item.auction_failures + 1
                        price = int(int(item.valuation_amount) * (0.8 if new_fail == 1 else 0.7))
                        update_sql = "UPDATE auction_item SET auction_failures=%s WHERE id=%s"
                        execute_with_retry(update_sql, [new_fail, item_id], item_id=item_id)

                        max_round = AuctionSchedule.objects.filter(auction_item_id=item_id).aggregate(Max('round_number'))['round_number__max'] or 0
                        next_round = max_round 
                        decision_round = next_round + 1
                        print(f"[삽입 시도 전] item_id={item_id}, next_round={next_round}, decision_round={decision_round}")
                        print(f"[DB 상태 확인]")
                        for r in AuctionSchedule.objects.filter(auction_item_id=item_id).order_by("round_number"):
                            print(f" - round={r.round_number}, type={r.schedule_type}, date={r.decision_date}")

                        t0 = decision_date + timezone.timedelta(minutes=30)

                        insert1 = (
                            "INSERT INTO auction_schedule "
                            "(auction_item_id,round_number,auction_date,schedule_type,minimum_price) "
                            "VALUES(%s,%s,%s,'매각기일',%s)"
                        )
                        insert2 = (
                            "INSERT INTO auction_schedule "
                            "(auction_item_id,round_number,decision_date,schedule_type,minimum_price) "
                            "VALUES(%s,%s,%s,'매각결정기일',0)"
                        )
                        execute_with_retry(insert1, [item_id, next_round, t0, price], item_id=item_id)
                        execute_with_retry(insert2, [item_id, decision_round, t0 + timezone.timedelta(minutes=30)], item_id=item_id)

            print("[process_due_auctions] 완료")
    except Timeout:
        print("[process_due_auctions] 다른 인스턴스 실행 중, 스킵")
