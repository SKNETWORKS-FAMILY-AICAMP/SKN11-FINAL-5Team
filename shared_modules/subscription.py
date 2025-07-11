# subscription.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import SubscriptionCreateWithPayment, SubscriptionResponse
from queries import create_subscription, simulate_payment
from typing import List

router = APIRouter()

@router.post("/subscribe/secure", response_model=SubscriptionResponse)
def subscribe_secure(data: SubscriptionCreateWithPayment, db: Session = Depends(get_db)):
    if not simulate_payment(data.user_id, data.monthly_fee):
        raise HTTPException(status_code=402, detail="결제 실패: 구독 생성이 차단됩니다.")
    return create_subscription(db, data.user_id, data.plan_type, data.monthly_fee)

@router.get("/admin/subscriptions", response_model=List[SubscriptionResponse])
def get_subscriptions(db: Session = Depends(get_db)):
    from queries import get_all_subscriptions
    return get_all_subscriptions(db)


#queries.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models import Subscription
from fastapi import HTTPException
import random


def simulate_payment(user_id: int, plan_type: str, amount: float) -> bool:
    """
    가상 결제 시뮬레이션 함수.
    실패 확률을 임의로 부여 (예: 10% 확률로 실패).
    """
    return random.random() > 0.1  # 90% 확률 성공


def create_subscription(
    db: Session,
    user_id: int,
    plan_type: str,
    monthly_fee: float,
    start_date: datetime,
    end_date: datetime,
) -> Subscription:
    if not simulate_payment(user_id, plan_type, monthly_fee):
        raise HTTPException(status_code=402, detail="결제 실패: 구독 생성이 차단되었습니다.")

    sub = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        monthly_fee=monthly_fee,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def get_active_subscriptions(db: Session):
    now = datetime.now(timezone.utc)
    return (
        db.query(Subscription)
        .filter(Subscription.end_date > now)
        .order_by(Subscription.end_date.asc())
        .all()
    )


def expire_old_subscriptions(db: Session) -> int:
    now = datetime.now(timezone.utc)
    expired = (
        db.query(Subscription)
        .filter(Subscription.end_date <= now)
        .all()
    )
    count = 0
    for sub in expired:
        db.delete(sub)
        count += 1
    db.commit()
    return count