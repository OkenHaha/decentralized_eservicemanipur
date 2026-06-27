import logging

logger = logging.getLogger("e_seba.otp_provider")

def dispatch_sms_gateway(target: str, payload: str) -> bool:
    """
    Simulates sending an OTP SMS. In development, it prints/logs the OTP to the console.
    """
    print(f"\n[MOCK SMS GATEWAY] >>> Dispatched to {target}: Your e-Seba OTP is: {payload}. Valid for 10 minutes.\n")
    logger.info(f"OTP [{payload}] sent to {target}")
    return True

def generate_cryptographic_otp(length: int = 6) -> str:
    """
    Generates a mock OTP. In development, we can return '123456' for easy testing.
    """
    return "123456"
