import os
import re
import ssl
import mimetypes
import smtplib
import logging
import base64
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from email.header import Header
from email import policy
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

class EmailManager:
    def is_valid_email(self, email: str) -> bool:
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

    async def send_email(self, service: str, to_emails: List[str], subject: str, body: str,
                         html_body: Optional[str] = None, attachments: List[str] = None,
                         cc_emails: List[str] = None, bcc_emails: List[str] = None,
                         from_email: Optional[str] = None, from_name: Optional[str] = None) -> Dict[str, Any]:
        for email in to_emails:
            if not self.is_valid_email(email):
                return {"success": False, "error": f"유효하지 않은 이메일 주소: {email}"}

        if service == "smtp":
            return await self.send_via_smtp(to_emails, subject, body, html_body, attachments, cc_emails, bcc_emails, from_email, from_name)
        elif service == "sendgrid":
            return await self.send_via_sendgrid(to_emails, subject, body, html_body, attachments, cc_emails, bcc_emails, from_email, from_name)
        elif service == "aws_ses":
            return await self.send_via_aws_ses(to_emails, subject, body, html_body, attachments, cc_emails, bcc_emails, from_email, from_name)
        else:
            return {"success": False, "error": f"지원하지 않는 이메일 서비스: {service}"}

    async def send_via_smtp(self, to_emails, subject, body, html_body, attachments, cc_emails, bcc_emails, from_email, from_name):
        print("[✅ DEBUG] 현재 실행 중인 send_via_smtp에는 Header 인코딩이 반영되어 있음")
        try:
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')

            if not smtp_user or not smtp_password:
                return {"success": False, "error": "SMTP 인증 정보가 없습니다."}

            sender_email = from_email or smtp_user
            sender_name = str(from_name or "자동 이메일 시스템")
            subject = str(subject or "")
            body = str(body or "")
            html_body = str(html_body) if html_body else None

            print("[📤 DEBUG] 발신자:", sender_name, sender_email)
            print("[📤 DEBUG] 제목:", subject)

            msg = EmailMessage(policy=policy.SMTPUTF8)
            msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
            msg['To'] = ', '.join(to_emails)
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            msg['Subject'] = str(Header(subject, 'utf-8'))
            msg['Message-ID'] = make_msgid()

            if html_body:
                msg.set_content(body, subtype='plain', charset='utf-8')
                msg.add_alternative(html_body, subtype='html', charset='utf-8')
            else:
                msg.set_content(body, charset='utf-8')

            for file_path in attachments or []:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        maintype, subtype = (mimetypes.guess_type(file_path)[0] or 'application/octet-stream').split('/')
                        msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(file_path))

            all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
            print("[📤 DEBUG] 전체 수신자:", all_recipients)

            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.send_message(msg, to_addrs=all_recipients)

            return {"success": True, "message_id": msg['Message-ID']}

        except Exception as e:
            logger.error(f"SMTP 이메일 발송 실패: {e}")
            return {"success": False, "error": str(e)}

    async def send_via_sendgrid(self, to_emails, subject, body, html_body, attachments, cc_emails, bcc_emails, from_email, from_name):
        if not SENDGRID_AVAILABLE:
            return {"success": False, "error": "sendgrid 모듈이 없습니다"}

        try:
            api_key = os.getenv('SENDGRID_API_KEY')
            default_email = os.getenv('SENDGRID_FROM_EMAIL')
            default_name = os.getenv('SENDGRID_FROM_NAME', '자동 이메일 시스템')
            sg = sendgrid.SendGridAPIClient(api_key=api_key)

            sender_email = from_email or default_email
            sender_name = from_name or default_name

            mail = Mail(
                from_email=Email(sender_email, sender_name),
                to_emails=[To(email) for email in to_emails],
                subject=subject,
                html_content=html_body if html_body else body
            )

            for cc in cc_emails or []:
                mail.add_cc(Email(cc))
            for bcc in bcc_emails or []:
                mail.add_bcc(Email(bcc))

            for file_path in attachments or []:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        encoded = base64.b64encode(f.read()).decode()
                        mail.add_attachment(Attachment(
                            file_content=FileContent(encoded),
                            file_name=FileName(os.path.basename(file_path)),
                            file_type=FileType(mimetypes.guess_type(file_path)[0] or 'application/octet-stream'),
                            disposition=Disposition('attachment')
                        ))

            response = sg.send(mail)
            return {"success": response.status_code in [200, 202], "status_code": response.status_code}

        except Exception as e:
            logger.error(f"SendGrid 이메일 발송 실패: {e}")
            return {"success": False, "error": str(e)}

    async def send_via_aws_ses(self, to_emails, subject, body, html_body, attachments, cc_emails, bcc_emails, from_email, from_name):
        if not BOTO3_AVAILABLE:
            return {"success": False, "error": "boto3가 설치되지 않았습니다."}

        try:
            ses = boto3.client(
                'ses',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )

            sender_email = from_email or os.getenv('SES_FROM_EMAIL')
            sender_name = str(from_name or "자동 이메일 시스템")
            subject = str(subject or "")
            body = str(body or "")
            html_body = str(html_body) if html_body else None

            msg = EmailMessage(policy=policy.SMTPUTF8)
            msg['Subject'] = str(Header(subject, 'utf-8'))
            msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
            msg['To'] = ', '.join(to_emails)

            if html_body:
                msg.set_content(body, subtype='plain', charset='utf-8')
                msg.add_alternative(html_body, subtype='html', charset='utf-8')
            else:
                msg.set_content(body, charset='utf-8')

            for file_path in attachments or []:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        maintype, subtype = (mimetypes.guess_type(file_path)[0] or 'application/octet-stream').split('/')
                        msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(file_path))

            response = ses.send_raw_email(
                Source=sender_email,
                Destinations=to_emails + (cc_emails or []) + (bcc_emails or []),
                RawMessage={'Data': msg.as_string()}
            )

            return {"success": True, "message_id": response['MessageId']}

        except ClientError as e:
            return {"success": False, "error": str(e.response['Error'])}
        except Exception as e:
            logger.error(f"SES 이메일 실패: {e}")
            return {"success": False, "error": str(e)}

_email_manager = None

def get_email_manager() -> EmailManager:
    global _email_manager
    if _email_manager is None:
        
        
    return _email_manager
