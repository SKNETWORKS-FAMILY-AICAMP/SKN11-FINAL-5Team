# /app/services/email_service.py
"""
통합 이메일 서비스
"""

import smtplib
from datetime import datetime
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import boto3
from botocore.exceptions import ClientError

from .common.base_service import BaseService
from .common.config_service import ConfigService

class EmailService(BaseService):
    """통합 이메일 발송 서비스"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, config)
        self.config_service = ConfigService(db_session, config)
        self.email_config = self.config_service.get_email_config()
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """이메일 발송 (설정에 따라 SMTP, AWS SES, SendGrid 중 선택)"""
        try:
            email_service = self.email_config.get("service", "smtp").lower()
            
            if email_service == "aws_ses":
                return await self._send_via_aws_ses(
                    to_emails, subject, body, html_body, attachments,
                    cc_emails, bcc_emails, from_email, from_name
                )
            elif email_service == "sendgrid":
                return await self._send_via_sendgrid(
                    to_emails, subject, body, html_body, attachments,
                    cc_emails, bcc_emails, from_email, from_name
                )
            else:  # SMTP 기본
                return await self._send_via_smtp(
                    to_emails, subject, body, html_body, attachments,
                    cc_emails, bcc_emails, from_email, from_name
                )
                
        except Exception as e:
            self.logger.error(f"이메일 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_via_smtp(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """SMTP를 통한 이메일 발송"""
        try:
            smtp_config = self.email_config.get("smtp", {})
            
            smtp_server = smtp_config.get("server", "smtp.gmail.com")
            smtp_port = smtp_config.get("port", 587)
            smtp_username = smtp_config.get("username")
            smtp_password = smtp_config.get("password")
            default_from_email = smtp_config.get("from_email", smtp_username)
            
            if not smtp_username or not smtp_password:
                return {"success": False, "error": "SMTP 인증 정보가 설정되지 않았습니다"}
            
            from_email = from_email or default_from_email
            from_display = f"{from_name} <{from_email}>" if from_name else from_email
            
            # 이메일 메시지 구성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_display
            msg['To'] = ', '.join(to_emails)
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 텍스트 부분 추가
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML 부분 추가
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 첨부파일 추가
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # 수신자 목록 구성
            all_recipients = to_emails[:]
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg, to_addrs=all_recipients)
            
            return {
                "success": True,
                "message_id": f"smtp_{datetime.now().timestamp()}",
                "recipients_count": len(all_recipients),
                "service": "smtp"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_via_aws_ses(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """AWS SES를 통한 이메일 발송"""
        try:
            ses_config = self.email_config.get("aws_ses", {})
            
            aws_region = ses_config.get("region", "us-east-1")
            default_from_email = ses_config.get("from_email")
            
            if not default_from_email:
                return {"success": False, "error": "발신자 이메일이 설정되지 않았습니다"}
            
            from_email = from_email or default_from_email
            source = f"{from_name} <{from_email}>" if from_name else from_email
            
            ses_client = boto3.client('ses', region_name=aws_region)
            
            # 수신자 구성
            destination = {
                'ToAddresses': to_emails
            }
            if cc_emails:
                destination['CcAddresses'] = cc_emails
            if bcc_emails:
                destination['BccAddresses'] = bcc_emails
            
            # 메시지 구성
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body, 'Charset': 'UTF-8'}
                }
            }
            
            if html_body:
                message['Body']['Html'] = {'Data': html_body, 'Charset': 'UTF-8'}
            
            # 첨부파일이 있는 경우 raw 메시지 사용
            if attachments:
                raw_message = self._create_raw_message(
                    from_email, to_emails, subject, body, html_body, 
                    attachments, cc_emails, bcc_emails, from_name
                )
                
                response = ses_client.send_raw_email(
                    Source=source,
                    Destinations=to_emails + (cc_emails or []) + (bcc_emails or []),
                    RawMessage={'Data': raw_message}
                )
            else:
                response = ses_client.send_email(
                    Source=source,
                    Destination=destination,
                    Message=message
                )
            
            return {
                "success": True,
                "message_id": response['MessageId'],
                "recipients_count": len(to_emails) + len(cc_emails or []) + len(bcc_emails or []),
                "service": "aws_ses"
            }
            
        except ClientError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_via_sendgrid(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """SendGrid를 통한 이메일 발송"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, To, Cc, Bcc, From, Content
            
            sendgrid_config = self.email_config.get("sendgrid", {})
            
            api_key = sendgrid_config.get("api_key")
            default_from_email = sendgrid_config.get("from_email")
            
            if not api_key:
                return {"success": False, "error": "SendGrid API 키가 설정되지 않았습니다"}
            
            if not default_from_email:
                return {"success": False, "error": "발신자 이메일이 설정되지 않았습니다"}
            
            from_email = from_email or default_from_email
            from_obj = From(from_email, from_name)
            
            # 수신자 구성
            to_list = [To(email) for email in to_emails]
            cc_list = [Cc(email) for email in (cc_emails or [])]
            bcc_list = [Bcc(email) for email in (bcc_emails or [])]
            
            # 메일 객체 생성
            mail = Mail(
                from_email=from_obj,
                to_emails=to_list,
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )
            
            if html_body:
                mail.content = [
                    Content("text/plain", body),
                    Content("text/html", html_body)
                ]
            
            # CC, BCC 추가
            if cc_list:
                mail.cc = cc_list
            if bcc_list:
                mail.bcc = bcc_list
            
            # 첨부파일 추가
            if attachments:
                for attachment in attachments:
                    self._add_sendgrid_attachment(mail, attachment)
            
            # 발송
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            response = sg.send(mail)
            
            return {
                "success": True,
                "message_id": response.headers.get('X-Message-Id'),
                "recipients_count": len(to_emails) + len(cc_emails or []) + len(bcc_emails or []),
                "service": "sendgrid",
                "status_code": response.status_code
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """SMTP/SES용 첨부파일 추가"""
        try:
            filename = attachment.get("filename")
            content = attachment.get("content")  # bytes
            content_type = attachment.get("content_type", "application/octet-stream")
            
            if not filename or not content:
                return
            
            part = MIMEBase(*content_type.split('/'))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            
        except Exception as e:
            self.logger.error(f"첨부파일 추가 실패: {e}")
    
    def _add_sendgrid_attachment(self, mail, attachment: Dict[str, Any]):
        """SendGrid용 첨부파일 추가"""
        try:
            from sendgrid.helpers.mail import Attachment
            import base64
            
            filename = attachment.get("filename")
            content = attachment.get("content")  # bytes
            content_type = attachment.get("content_type", "application/octet-stream")
            
            if not filename or not content:
                return
            
            encoded_content = base64.b64encode(content).decode()
            
            attachment_obj = Attachment(
                file_content=encoded_content,
                file_name=filename,
                file_type=content_type,
                disposition="attachment"
            )
            
            mail.attachment = [attachment_obj]
            
        except Exception as e:
            self.logger.error(f"SendGrid 첨부파일 추가 실패: {e}")
    
    def _create_raw_message(
        self,
        from_email: str,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str],
        attachments: List[Dict[str, Any]],
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        from_name: Optional[str] = None
    ) -> str:
        """첨부파일이 있는 경우 raw 메시지 생성"""
        try:
            from_display = f"{from_name} <{from_email}>" if from_name else from_email
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = from_display
            msg['To'] = ', '.join(to_emails)
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 텍스트 부분
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML 부분
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 첨부파일
            for attachment in attachments:
                self._add_attachment(msg, attachment)
            
            return msg.as_string()
            
        except Exception as e:
            self.logger.error(f"Raw 메시지 생성 실패: {e}")
            return ""
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        return {
            "service": "email_service",
            "status": "healthy",
            "configured_service": self.email_config.get("service", "smtp"),
            "service_enabled": self.config_service.is_service_enabled("email")
        }
    
    async def cleanup(self):
        """서비스 정리"""
        await self.config_service.cleanup()
        self.logger.info("이메일 서비스 정리 완료")