"""
Mental Agent 모델 정의
Fully qualified path 사용으로 SQLAlchemy 충돌 완전 방지
"""

import sys
import os

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "../shared_modules"))

# SQLAlchemy 충돌 방지를 위해 fully qualified import 사용
import shared_modules.db_models as db_models

# Mental Agent는 이제 모든 모델을 fully qualified path로 접근합니다
# Report 모델도 이제 공통 모듈에 포함되어 있습니다

# 기존 코드와의 호환성을 위한 별칭들 (fully qualified path 사용)
DBUser = db_models.User
DBConversation = db_models.Conversation
DBMessage = db_models.Message
DBAutomationTask = db_models.AutomationTask
DBPHQ9Result = db_models.PHQ9Result
DBReport = db_models.Report
DBTemplateMessage = db_models.TemplateMessage
DBFAQ = db_models.FAQ
DBFeedback = db_models.Feedback
DBSubscription = db_models.Subscription