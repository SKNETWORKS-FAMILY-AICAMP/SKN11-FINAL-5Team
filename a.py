# import os
# from shared_modules import get_session_context
# from sqlalchemy.sql import text
# from datetime import datetime

# # === 설정 ===
# html_file_path = "C:/TinkerBell/lean-canvas-common.html"
# user_id = 3
# title = "린 캔버스_common"
# report_type = "린캔버스"
# conversation_id = None  # 없으면 NULL 저장됨

# # === HTML 읽기 ===
# if not os.path.isfile(html_file_path):
#     raise FileNotFoundError(f"파일을 찾을 수 없습니다: {html_file_path}")

# with open(html_file_path, "r", encoding="utf-8") as f:
#     html_content = f.read()

# # === DB 삽입 ===
# with get_session_context() as db:
#     insert_query = text("""
#         INSERT INTO report (user_id, conversation_id, report_type, title, content_data, file_url, created_at)
#         VALUES (:user_id, :conversation_id, :report_type, :title, :content_data, :file_url, :created_at)
#     """)
#     result = db.execute(
#         insert_query,
#         {
#             "user_id": user_id,
#             "conversation_id": conversation_id,
#             "report_type": report_type,
#             "title": title,
#             "content_data": html_content,
#             "file_url": "https://example.com/file/report-test.pdf",
#             "created_at": datetime.now()
#         }
#     )
#     db.commit()
#     print(f"✅ 리포트 '{title}' 이(가) 성공적으로 저장되었습니다.")


import os
from shared_modules import get_session_context
from shared_modules.queries import create_template_message

# === 설정 ===
html_file_path = "C:/TinkerBell/lean-canvas-common.html"
user_id = 3
title = "린 캔버스_common"
channel_type = "EMAIL"  # 반드시 대문자여야 함
content_type = "html"
template_type = "린캔버스"

# === HTML 읽기 ===
if not os.path.isfile(html_file_path):
    raise FileNotFoundError(f"파일을 찾을 수 없습니다: {html_file_path}")

with open(html_file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# === DB 삽입 ===
with get_session_context() as db:
    result = create_template_message(
        db=db,
        user_id=user_id,
        template_type=template_type,
        channel_type=channel_type,
        title=title,
        content=html_content,
        content_type=content_type
    )

    if result:
        print(f"✅ 템플릿 '{title}'이(가) 성공적으로 저장되었습니다.")
    else:
        print(f"❌ 템플릿 저장 실패")
