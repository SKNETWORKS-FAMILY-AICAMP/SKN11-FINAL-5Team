# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from unified_agent_system.database import get_db
# from shared_modules.db_models import TemplateMessage
# from schemas import EmailTemplateCreate, EmailTemplateUpdate
# from datetime import datetime
# from sqlalchemy import not_, or_

# router = APIRouter()

# # 프론트에 맞게 직렬화
# def serialize_template(template: TemplateMessage):
#     return {
#         "id": template.template_id,
#         "title": template.title,
#         "content": template.content,
#         "createdAt": template.created_at.strftime("%Y-%m-%d"),
#         "contentType": template.content_type,
#     }

# # 템플릿 + 사용자 콘텐츠 가져오기
# @router.get("/email")
# def get_email_templates(user_id: int, db: Session = Depends(get_db)):
#     # 관리자 템플릿
#     templates = (
#         db.query(TemplateMessage)
#         .filter(TemplateMessage.channel_type == "EMAIL")
#         .filter(TemplateMessage.user_id == 3)
#         .filter(
#     not_(TemplateMessage.template_type.in_(["린캔버스", "user_made"]))
# )
#         .order_by(TemplateMessage.created_at.desc())
#         .all()
#     )

#     # 사용자 작성 콘텐츠
#     contents = (
#         db.query(TemplateMessage)
#         .filter(TemplateMessage.channel_type == "EMAIL")
#         .filter(TemplateMessage.user_id == user_id)
#         .filter(TemplateMessage.template_type == "user_made")
#         .order_by(TemplateMessage.created_at.desc())
#         .all()
#     )

#     return {
#         "email_templates": [serialize_template(t) for t in templates],
#         "email_contents": [serialize_template(c) for c in contents]
#     }

# # 사용자 이메일 콘텐츠 생성
# @router.post("/email")
# def create_email_template(data: EmailTemplateCreate, db: Session = Depends(get_db)):
#     new_template = TemplateMessage(
#         user_id=data.user_id,
#         title=data.title,
#         content=data.content,
#         template_type="user_made",  # 사용자 생성
#         channel_type=data.channel_type,
#         content_type=data.content_type,
#         created_at=datetime.now(),
#     )
#     db.add(new_template)
#     db.commit()
#     db.refresh(new_template)
#     return {"message": "Created", "template_id": new_template.template_id}

# # 콘텐츠 수정
# @router.put("/email/{template_id}")
# def update_email_template(template_id: int, update: EmailTemplateUpdate, db: Session = Depends(get_db)):
#     template = db.query(TemplateMessage).filter(TemplateMessage.template_id == template_id).first()
#     if not template:
#         raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")

#     if update.title:
#         template.title = update.title
#     if update.content:
#         template.content = update.content
#     template.updated_at = datetime.utcnow()

#     db.commit()
#     return {"message": "이메일 템플릿이 수정되었습니다."}
