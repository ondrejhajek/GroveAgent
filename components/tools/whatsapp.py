import os
import requests
from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field


class WhatsAppParams(BaseModel):
    message: str = Field(description="Zpráva, která bude odeslána na WhatsApp")


class WhatsAppResult(BaseModel):
    success: bool = Field(description="Zda byla zpráva úspěšně odeslána")
    status_code: int = Field(description="HTTP stavový kód odpovědi z API")
    message: str = Field(description="Zpráva o výsledku odeslání")


def whatsapp(ctx: RunContext, params: WhatsAppParams) -> WhatsAppResult:

    api_key = os.environ.get("CALLMEBOT_API_KEY")
    phone = os.environ.get("CALLMEBOT_PHONE")

    response = requests.get(
        "https://api.callmebot.com/whatsapp.php",
        params={
            "phone": phone,
            "text": params.message,
            "apikey": api_key,
        },
    )

    print(response.status_code)

    if response.ok:
        return WhatsAppResult(
            success=True,
            status_code=response.status_code,
            message="Zpráva byla úspěšně odeslána na WhatsApp",
        )
    else:
        return WhatsAppResult(
            success=False,
            status_code=response.status_code,
            message=f"Odeslání selhalo: {response.text}",
        )


tool = Tool(whatsapp, description="Odeslání WhatsApp zprávy")
