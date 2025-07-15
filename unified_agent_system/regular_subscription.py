# ✅ 전체 통합 정기결제 시스템 (FastAPI)


from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import requests
import os
import sys

# 경로 설정 (shared_modules import용)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_modules.database import get_session_context
from shared_modules.db_models import Subscription
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()
router = APIRouter()

# ✅ DB 초기화용 스케줄러 생성
scheduler = BackgroundScheduler()

# ✅ 결제 준비 API
class SubscriptionRequest(BaseModel):
    user_id: int
    plan_type: str
    monthly_fee: float

@router.post("/subscription/ready")
def subscription_ready(data: SubscriptionRequest):
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=30)
    with get_session_context() as db:
        existing = db.query(Subscription).filter(Subscription.user_id == data.user_id).first()

        if existing:
            remaining_days = max((existing.end_date.replace(tzinfo=timezone.utc) - now).days, 0) + 1
            total_days = (existing.end_date.replace(tzinfo=timezone.utc) - existing.start_date.replace(tzinfo=timezone.utc)).days or 30
            previous_value = float(existing.monthly_fee) * (remaining_days / total_days)
            partial_payment = round(data.monthly_fee - previous_value, 2)
        else:
            partial_payment = data.monthly_fee

        temp_data = {
            "cid": os.getenv("KAKAOPAY_REG_CID"),
            "partner_order_id": f"order_{data.user_id}",
            "partner_user_id": str(data.user_id),
            "item_name": f"{data.plan_type} 구독",
            "quantity": 1,
            "total_amount": int(partial_payment),
            "vat_amount": 0,
            "tax_free_amount": 0,
            "approval_url": f"http://localhost:8080/subscription/approve?user_id={data.user_id}&plan_type={data.plan_type}&monthly_fee={data.monthly_fee}",
            "cancel_url": "http://localhost:8080/subscription/cancel",
            "fail_url": "http://localhost:8080/subscription/fail"
        }

        headers = {
            "Authorization": f"SECRET_KEY {os.getenv('KAKAOPAY_SECRET_DEV')}",
            "Content-Type": "application/json"
        }

        response = requests.post("https://open-api.kakaopay.com/online/v1/payment/ready", headers=headers, json=temp_data)
        response.raise_for_status()
        result = response.json()

        if existing:
            existing.tid = result["tid"]
            existing.status = "PENDING"
        else:
            db.add(Subscription(user_id=data.user_id, plan_type=data.plan_type, monthly_fee=data.monthly_fee, tid=result["tid"], start_date=now, end_date=end, status="PENDING"))

        db.commit()

        return {"redirect_url": result["next_redirect_pc_url"]}

# ✅ 결제 승인 API
@router.get("/subscription/approve")
def payment_approve(pg_token: str = Query(...), user_id: int = Query(...), plan_type: str = Query(...), monthly_fee: float = Query(...)):
    with get_session_context() as db:
        sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if not sub or not sub.tid:
            raise HTTPException(status_code=404, detail="구독 정보 없음")

        headers = {
            "Authorization": f"KakaoAK {os.getenv('KAKAO_ADMIN_KEY')}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }

        data = {
            "cid": os.getenv("KAKAOPAY_REG_CID"),
            "tid": sub.tid,
            "partner_order_id": f"order_{user_id}",
            "partner_user_id": str(user_id),
            "pg_token": pg_token
        }

        response = requests.post("https://kapi.kakao.com/v1/payment/approve", headers=headers, data=data)
        result = response.json()
        print(result)

        sub.sid = result.get("sid")
        sub.plan_type = plan_type
        sub.monthly_fee = monthly_fee
        sub.start_date = datetime.now(timezone.utc)
        sub.end_date = sub.start_date + timedelta(days=30)
        sub.status = "ACTIVE"

        db.commit()
        return {"success": True, "subscription_id": sub.subscription_id}

# ✅ 해지 API
def cancel_kakaopay_payment(tid: str, cancel_amount: float):
    url = "https://open-api.kakaopay.com/online/v1/payment/cancel"
    headers = {
        "Authorization": f"SECRET_KEY {os.getenv('KAKAOPAY_SECRET_DEV')}",
        "Content-Type": "application/json"
    }
    payload = {
        "cid": os.getenv('KAKAOPAY_CID'),
        "tid": tid,
        "cancel_amount": cancel_amount,
        "cancel_tax_free_amount": 0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"KakaoPay 결제 취소 실패: {response.text}")
    return response.json()

@router.post("/subscription/cancel")
def cancel_subscription(user_id: int = Query(...)):
    with get_session_context() as db:
        sub: Subscription = db.query(Subscription).filter_by(user_id=user_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="구독 정보를 찾을 수 없습니다.")

        now = datetime.utcnow()

        if sub.end_date and sub.end_date < now:
            raise HTTPException(status_code=400, detail="이미 종료된 구독입니다.")

        if not sub.tid:
            raise HTTPException(status_code=400, detail="결제 TID가 존재하지 않습니다.")

        # 날짜 계산
        total_days = (sub.end_date - sub.start_date).days or 30
        remaining_days = max((sub.end_date - now).days, 0)

        # 환불 금액 계산
        refund_amount = round(float(sub.monthly_fee) * (remaining_days / total_days), 2)

        # 카카오페이 결제 취소
        try:
            cancel_response = cancel_kakaopay_payment(sub.tid, refund_amount)
        except HTTPException as e:
            raise e

        # 구독 해지 처리
        sub.plan_type = "basic"
        sub.monthly_fee = 0
        sub.sid = None
        sub.end_date = now

        db.commit()

        return {
            "success": True,
            "message": "구독이 해지되었으며 결제가 취소되었습니다.",
            "refund_amount": refund_amount,
            "remaining_days": remaining_days,
            "kakaopay_response": cancel_response
        }

# ✅ 다운그레이드 처리
@router.post("/subscription/downgrade")
def downgrade_subscription(user_id: int, new_fee: float):
    with get_session_context() as db:
        sub = db.query(Subscription).filter_by(user_id=user_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="구독 정보 없음")

        now = datetime.now(timezone.utc)

        # 👉 end_date가 naive datetime이면 timezone-aware로 변환
        if sub.end_date.tzinfo is None:
            sub_end_date = sub.end_date.replace(tzinfo=timezone.utc)
        else:
            sub_end_date = sub.end_date

        remaining_days = max((sub_end_date - now).days, 0)
        current_value = float(sub.monthly_fee) * (remaining_days / 30)
        refund = round(current_value - new_fee, 2) if current_value > new_fee else 0

        if new_fee == 0:
            new_plan = "basic"
        elif new_fee == 2900:
            new_plan = "premium"
        else:
            new_plan = "enterprise"

        sub.plan_type = new_plan
        sub.monthly_fee = new_fee
        db.commit()

        return {
            "success": True,
            "refund_amount": refund,
            "remaining_days": remaining_days,
            "current_value": round(current_value, 2),
            "new_fee": new_fee
        }

# ✅ 정기결제 스케줄러
@scheduler.scheduled_job("cron", hour=0)
def run_recurring_payments():
    with get_session_context() as db:
        today = datetime.now(timezone.utc).date()
        subs = db.query(Subscription).filter(Subscription.status == "ACTIVE").all()
        for sub in subs:
            if sub.end_date.date() <= today:
                data = {
                    "cid": os.getenv("KAKAOPAY_REG_CID"),
                    "sid": sub.sid,
                    "partner_order_id": f"order_{sub.user_id}_{today}",
                    "partner_user_id": str(sub.user_id),
                    "quantity": 1,
                    "total_amount": int(sub.monthly_fee),
                    "item_name": sub.plan_type
                }
                headers = {
                    "Authorization": f"SECRET_KEY {os.getenv('KAKAOPAY_SECRET_DEV')}",
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
                }
                try:
                    res = requests.post("https://open-api.kakaopay.com/online/v1/payment/subscription", headers=headers, data=data)
                    res.raise_for_status()
                    sub.start_date = sub.end_date
                    sub.end_date = sub.start_date + timedelta(days=30)
                    db.commit()
                except:
                    sub.status = "EXPIRED"
                    db.commit()

scheduler.start()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("subscription:app", host="127.0.0.1", port=8080, reload=True)
