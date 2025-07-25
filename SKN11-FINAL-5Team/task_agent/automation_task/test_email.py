import asyncio
from dotenv import load_dotenv
from task_agent.automation_task.email_service import send_email_smtp, send_email_sendgrid, send_email_aws_ses

load_dotenv(dotenv_path="../../unified_agent_system/.env")  # 혹시 몰라 안전하게 다시 호출

async def main():
    to_emails = ["donggle0519@naver.com"]
    subject = "안녕"
    body = ""
    html_body="""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>생일 축하 템플릿</title>
  <link href="https://fonts.googleapis.com/css?family=Lora:400,400i,700,700i" rel="stylesheet">
  <style>
    body { font-family: 'Lora', Georgia, 'Times New Roman', serif; background:#f6f6f6; }
    .preview-container {
      background:#fff;
      border-radius:10px;
      box-shadow:0 2px 8px #eee;
      width:600px;
      margin:40px auto 0 auto;
      font-family: 'Lora', Georgia, 'Times New Roman', serif;
    }
    .es-header-row {
      display: flex;
      align-items: center;
      padding: 15px 20px 15px 20px;
    }
    .es-header-left {
      color:#CCCCCC;
      font-size:14px;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-title {
      font-family:Lora,Georgia,'Times New Roman',serif;
      color:#666;
      font-size:40px;
      text-align:center;
      margin:36px 0 0 0;
      font-weight:normal;
    }
    .email-img { display:block; margin:28px auto 24px auto; }
    .email-body {
      color:#999999;
      font-size:14px;
      text-align:center;
      line-height:1.7;
      margin-bottom:20px;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-sign {
      color:#999;
      font-size:14px;
      text-align:center;
      font-style:italic;
      margin-bottom:36px;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-surprise {
      background:#c4dbf2;
      padding:36px 0 36px 0;
      text-align:center;
    }
    .email-surprise-title {
      color:#2f464b;
      font-size:24px;
      margin:0 0 12px 0;
      font-weight:normal;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-surprise-desc {
      color:#2f464b;
      font-size:20px;
      margin:0 0 18px 0;
      font-weight:normal;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-btn {
      display:inline-block;
      background:#fff;
      color:#2f464b;
      padding:10px 25px;
      border-radius:5px;
      text-decoration:none;
      font-size:18px;
      border:1px solid #ddd;
      margin-bottom:10px;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-footer {
      text-align:center;
      padding:32px 0 0 0;
      font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    }
    .email-brand {
      font-size:24px;
      color:#222;
      font-weight:normal;
      letter-spacing:2px;
      margin-bottom:10px;
    }
    .email-copyright {
      color:#888;
      font-size:12px;
      margin-bottom:4px;
    }
    .email-unsub {
      color:#888;
      font-size:12px;
      text-decoration:underline;
    }
    .footer-spacer {
      height: 48px;
      background: transparent;
    }
  </style>
</head>
<body>

      <div class="preview-container">
        <div class="es-header-row">
          <div class="es-header-left">TinkerBell</div>
        </div>
        <div style="background:#fff;">
          <div class="email-title"><em>Happy Birthday!</em></div>
          <img class="email-img" src="https://fveetos.stripocdn.email/content/guids/CABINET_b54797fc68edcecf4f6b2835e7bcba32/images/36321522405737710.gif" width="300" alt="Gift">
          <div style="padding:30px 40px 40px 40px;">
            <div class="email-body">
              팅커벨님, 생일을 진심으로 축하드립니다!<br>
              오늘 하루, 소중한 분과 행복한 시간 보내시길 바랍니다.<br>
              감사의 마음을 담아 5000원 할인 쿠폰을 선물로 드립니다.
            </div>
            <div class="email-sign">TinkerBell 배상</div>
          </div>
        </div>
        <div class="email-surprise">
          <div class="email-surprise-title">Surprise!</div>
          <div class="email-surprise-desc">
            For the next week you can get <span>5000 won</span> off premium status.
          </div>
          <a href="https://yourshop.com/gift" class="email-btn" target="_blank">Claim this Gift</a>
        </div>
        <div class="email-footer">
          
          <div class="email-brand">팅커벨</div>
          <div class="email-copyright">
            Copyright © 2028 TinkerBell, All rights reserved.<br>
            You are receiving this email because you have visited our site or asked us about regular newsletter.
          </div>
          <a href="#" class="email-unsub">Unsubscribe</a>
          <div class="footer-spacer"></div>
        </div>
      </div>
    
</body>
</html>"""
    attachments = []  # 필요하면 ["./파일.pdf"]

    # SMTP
    result_smtp = await send_email_smtp(
        None,
        to_emails=to_emails,
        subject=subject,
        body=body,
        html_body=html_body
    )
    print("[SMTP] ", result_smtp)

    # SendGrid
    result_sendgrid = await send_email_sendgrid(
        None,
        to_emails=to_emails,
        subject=subject,
        body=body,
        html_body=html_body
    )
    print("[SendGrid] ", result_sendgrid)

    # AWS SES
    result_ses = await send_email_aws_ses(
        None,
        to_emails=to_emails,
        subject=subject,
        body=body,
        html_body=html_body
    )
    print("[SES] ", result_ses)

if __name__ == "__main__":
    asyncio.run(main())
