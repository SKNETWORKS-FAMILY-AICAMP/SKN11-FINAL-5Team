
"""
SMS 발송 서비스
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional

from .common.base_service import BaseService
from .common.config_service import ConfigService

class SMSService(BaseService):
    """SMS 발송 서비스"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session, config)
        self.config_service = ConfigService(db_session, config)
        self.sms_config = self.config_service.get_sms_config()
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """SMS 발송"""
        try:
            # 메시지 길이 제한 (160자)
            if len(message) > 160:
                message = message[:157] + "..."
            
            sms_service = self.sms_config.get("service", "aws_sns").lower()
            
            if sms_service == "aws_sns":
                return await self._send_via_aws_sns(phone_number, message)
            else:
                return {"success": False, "error": f"지원하지 않는 SMS 서비스: {sms_service}"}
                
        except Exception as e:
            self.logger.error(f"SMS 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_via_aws_sns(self, phone_number: str, message: str) -> Dict[str, Any]:
        """AWS SNS를 통한 SMS 발송"""
        try:
            sns_config = self.sms_config.get("aws_sns", {})
            aws_region = sns_config.get("region", "us-east-1")
            
            sns_client = boto3.client('sns', region_name=aws_region)
            
            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            return {
                "success": True,
                "message_id": response['MessageId'],
                "service": "aws_sns"
            }
            
        except ClientError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_bulk_sms(self, phone_numbers: list, message: str) -> Dict[str, Any]:
        """벌크 SMS 발송"""
        try:
            results = []
            
            for phone_number in phone_numbers:
                result = await self.send_sms(phone_number, message)
                results.append({
                    "phone_number": phone_number,
                    "result": result
                })
            
            successful = [r for r in results if r["result"].get("success")]
            failed = [r for r in results if not r["result"].get("success")]
            
            return {
                "success": len(successful) > 0,
                "total_sent": len(phone_numbers),
                "success_count": len(successful),
                "failed_count": len(failed),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"벌크 SMS 발송 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        return {
            "service": "sms_service",
            "status": "healthy",
            "configured_service": self.sms_config.get("service", "aws_sns"),
            "service_enabled": self.config_service.is_service_enabled("sms")
        }
    
    async def cleanup(self):
        """서비스 정리"""
        await self.config_service.cleanup()
        self.logger.info("SMS 서비스 정리 완료")