_Aktualizováno: 2026-04-30_

# Tools

Tools jsou Python funkce zabalené do `pydantic_ai.Tool`, které agent může volat při zpracování požadavku. Načítají se přes `FunctionToolset` na základě konfigurace v `config.yaml`.

---

## Konfigurace

```yaml
agent:
  tools:
    - <název_toolu>
    - <název_toolu>
```

Název odpovídá názvu souboru v `system/components/tools/` (nebo `components/tools/` pro projektové přepsání), bez přípony `.py`.

---

## Dostupné tools

### `mailgun_mailer`

**Soubor:** `system/components/tools/mailgun_mailer.py`

Odešle emailovou zprávu přes Mailgun API. Volitelně podporuje přílohu ve formátu base64. Odesílatel se načítá z proměnné prostředí `MAILGUN_FROM_EMAIL`, doména je odvozena z této adresy.

**Vyžadované env proměnné:**

| Proměnná | Popis |
|---|---|
| `MAILGUN_API_KEY` | API klíč Mailgun účtu |
| `MAILGUN_FROM_EMAIL` | Odesílací emailová adresa (určuje i doménu) |

**Parametry (`MailgunMailerParams`):**

| Parametr | Typ | Povinný | Popis |
|---|---|---|---|
| `to_email` | `str` | ano | Emailová adresa příjemce |
| `subject` | `str` | ano | Předmět zprávy |
| `text` | `str` | ano | Tělo zprávy v prostém textu |
| `attachment_base64` | `str` | ne | Base64 enkódovaný obsah přílohy |
| `attachment_extension` | `str` | ne | Přípona souboru přílohy, např. `pdf`, `png` |

**Výsledek (`MailgunMailerResult`):**

| Pole | Typ | Popis |
|---|---|---|
| `success` | `bool` | Zda byl email úspěšně odeslán |
| `to_email` | `str` | Adresa příjemce |
| `status_code` | `int` | HTTP stavový kód odpovědi z Mailgun |
| `message` | `str` | Popis výsledku |

---

### `run_bash`

**Soubor:** `system/components/tools/run_bash.py`

Spustí bash příkaz nebo skript v shellu. Příkazy jsou před spuštěním kontrolovány bezpečnostním filtrem — zakázané vzory jsou odmítnuty bez provedení. Pracovní adresář je nastaven na `storage/`.

**Limity:**

| Limit | Hodnota |
|---|---|
| Maximální délka skriptu | 2 000 znaků |
| Timeout | 30 sekund |
| Maximální délka stdout | 10 000 znaků |
| Maximální délka stderr | 2 000 znaků |

**Pracovní adresář:** vždy `storage/` (hardcoded, nelze změnit)

**Blokované vzory (příklady):**

- `rm -rf /` — mazání kořenového adresáře
- `dd of=/dev/...` — přímý zápis na zařízení
- `curl ... | bash`, `wget ... | bash` — stažení a spuštění kódu
- `shutdown`, `reboot`, `halt` — vypnutí systému
- `systemctl stop/disable/mask` — zastavení systémových služeb
- `: () { ... }` — fork bomb
- `passwd`, `useradd`, `userdel` — správa uživatelů

**Parametry (`RunBashParams`):**

| Parametr | Typ | Popis |
|---|---|---|
| `script` | `str` | Bash příkaz nebo skript k vykonání |

**Výsledek (`RunBashResult`):**

| Pole | Typ | Popis |
|---|---|---|
| `success` | `bool` | Zda příkaz skončil s návratovým kódem 0 |
| `return_code` | `int` | Návratový kód procesu |
| `stdout` | `str` | Standardní výstup |
| `stderr` | `str` | Chybový výstup |
| `blocked` | `bool` | Zda byl příkaz zablokován bezpečnostní kontrolou |
| `blocked_reason` | `str` | Důvod zablokování (pokud byl zablokován) |

---

### `whatsapp`

**Soubor:** `system/components/tools/whatsapp.py`

Odešle WhatsApp zprávu přes CallMeBot API. Číslo příjemce a API klíč jsou načítány z proměnných prostředí — agent zadává pouze text zprávy.

**Vyžadované env proměnné:**

| Proměnná | Popis |
|---|---|
| `CALLMEBOT_API_KEY` | API klíč CallMeBot účtu |
| `CALLMEBOT_PHONE` | Telefonní číslo příjemce ve formátu s předvolbou, např. `+420123456789` |

**Parametry (`WhatsAppParams`):**

| Parametr | Typ | Popis |
|---|---|---|
| `message` | `str` | Text zprávy k odeslání |

**Výsledek (`WhatsAppResult`):**

| Pole | Typ | Popis |
|---|---|---|
| `success` | `bool` | Zda byla zpráva úspěšně odeslána |
| `status_code` | `int` | HTTP stavový kód odpovědi z CallMeBot |
| `message` | `str` | Popis výsledku |

---

## Přidání vlastního toolu

1. Vytvoř soubor `system/components/tools/<název>.py` (nebo `components/tools/<název>.py` pro projektové přepsání).
2. Definuj Pydantic modely pro parametry a výsledek.
3. Implementuj funkci s podpisem `def my_tool(ctx: RunContext, params: MyParams) -> MyResult`.
4. Exportuj instanci jako `tool = Tool(my_tool, description="...")`.
5. Přidej `<název>` do seznamu `tools` v `config.yaml`.

```python
from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field

class MyParams(BaseModel):
    value: str = Field(description="Vstupní hodnota")

class MyResult(BaseModel):
    output: str = Field(description="Výsledek operace")

def my_tool(ctx: RunContext, params: MyParams) -> MyResult:
    """Popis toolu viditelný agentem."""
    return MyResult(output=f"zpracováno: {params.value}")

tool = Tool(my_tool, description="Stručný popis pro agenta")
```

```yaml
agent:
  tools:
    - my_tool
```
