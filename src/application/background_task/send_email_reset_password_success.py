from fastapi_mail import FastMail, MessageSchema, MessageType
from ...infrastructure.config.mailing import mail_config

async def send_email_reset_password_success(email: str) -> None:
    message = MessageSchema(
        subject="Anteiku Kohi - Thông báo",
        recipients=[email],
        body="""
           	<div>
                <div style="margin-bottom: 20px; color: black;">
                    <p>Bạn đã thay đổi mật khẩu thành công. Nếu đây là hành động của bạn, xin hãy bỏ qua email này.</p>
                </div>
                <div style="margin-bottom: 4px; color: black;">
               	    <p>Trân trọng,</p>
                </div>
                <div style="color: black;">
               	    <strong><p>Anteiku Kohi</p></strong>
                </div>
            </div>
        """,
        subtype=MessageType.html
    )
    fm = FastMail(mail_config)
    await fm.send_message(message)
