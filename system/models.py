from typing import Type, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- Obálka zprávy pro broker ---

class BrokerMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: str
    data: BaseModel


# --- Definice modelů ---

class CronEvent(BaseModel):
    interval: str = Field(..., description="Cron výraz, který událost spustil")
    fired_at: str = Field(..., description="ISO timestamp okamžiku spuštění")
    current_time: str = Field(..., description="Aktuální čas, datum a den v týdnu")
    prompt: str = Field(..., description="Instrukce co s daty udělat")


class FileEvent(BaseModel):
    event: str = Field(..., description="Typ události, např. 'new_file'")
    path: str = Field(..., description="Cesta k souboru")
    data: str = Field(..., description="Nová data v souboru")
    prompt: str = Field(..., description="Instrukce co s daty udělat")


class DirWatchEvent(BaseModel):
    path: str = Field(..., description="Cesta k nově vytvořenému souboru")
    extension: str = Field(..., description="Přípona souboru")
    prompt: str = Field(..., description="Instrukce co s daty udělat")


# --- Dynamická továrna ---

def get_model_instance(model_name: str, payload: dict) -> Optional[BaseModel]:
    #Dynamicky vyhledá třídu v tomto modulu a vytvoří její instanci.
    # Vyhledá objekt v aktuálním modulu (models.py)
    model_cls: Optional[Type[BaseModel]] = globals().get(model_name)
    # Ověříme, že jde o validní Pydantic třídu
    if model_cls and isinstance(model_cls, type) and issubclass(model_cls, BaseModel):
        return model_cls(**payload)
    return None