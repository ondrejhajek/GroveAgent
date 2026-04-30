import os
import base64
import requests
from typing import Optional
from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field

class MailgunMailerParams(BaseModel):
    to_email: str
    subject: str
    text: str
    attachment_base64: Optional[str] = Field(default=None, description="Base64 enkódovaný obsah přílohy")
    attachment_extension: Optional[str] = Field(default=None, description="Přípona souboru přílohy (např. pdf, png)")

class MailgunMailerResult(BaseModel):
    success: bool = Field(description="Zda byl email úspěšně odeslán")
    to_email: str = Field(description="Emailová adresa příjemce")
    status_code: int = Field(description="HTTP stavový kód odpovědi z Mailgun API")
    message: str = Field(description="Zpráva o výsledku odeslání")

def mailgun_mailer(ctx: RunContext, params: MailgunMailerParams) -> MailgunMailerResult:

    from_email = os.environ.get("MAILGUN_FROM_EMAIL")

    domain = from_email.split("@")[-1]

    files = None
    if params.attachment_base64 and params.attachment_extension:
        filename = f"attachment.{params.attachment_extension.lstrip('.')}"
        file_bytes = base64.b64decode(params.attachment_base64)
        files = [("attachment", (filename, file_bytes))]

    response = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", os.environ.get("MAILGUN_API_KEY")),
        data={
            "from": from_email,
            "to": params.to_email,
            "subject": params.subject,
            "text": params.text,
        },
        files=files,
    )

    if response.ok:
        return MailgunMailerResult(
            success=True,
            to_email=params.to_email,
            status_code=response.status_code,
            message=f"Email byl úspěšně odeslán na adresu {params.to_email}",
        )
    else:
        return MailgunMailerResult(
            success=False,
            to_email=params.to_email,
            status_code=response.status_code,
            message=f"Odeslání selhalo: {response.text}",
        )

tool = Tool(mailgun_mailer, description="Odeslání emailové zprávy")
