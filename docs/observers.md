# Observers

Observery jsou komponenty, které sledují externí události a při jejich vzniku publikují zprávu do RabbitMQ brokeru. Agent ji zpracuje na základě přiloženého `prompt`u.

Každý observer běží v samostatném daemonic vlákně a komunikuje s hlavní smyčkou přes `asyncio.run_coroutine_threadsafe`.

---

## Konfigurace

Observery se definují v `config.yaml` pod klíčem `observers`:

```yaml
observers:
  - enabled: true
    type: <typ>
    parameters:
      <parametry specifické pro typ>
    prompt: "Co má agent udělat po přijetí události"
```

| Pole | Popis |
|---|---|
| `enabled` | `true` / `false` — zda se observer spustí při startu |
| `type` | Identifikátor observeru — název modulu v `system/components/observers/` |
| `parameters` | Slovník parametrů předaných metodě `run()` |
| `prompt` | Instrukce pro agenta přiložená ke každé publikované události |

---

## Dostupné observery

### `cron`

**Soubor:** `system/components/observers/cron.py`

Periodicky spouští agenta podle cron výrazu. Používá knihovnu `croniter`.

**Parametry:**

| Parametr | Typ | Popis |
|---|---|---|
| `interval` | `str` | Cron výraz, např. `"*/5 * * * *"` |

**Publikovaná událost:** `CronEvent`

| Pole | Popis |
|---|---|
| `interval` | Cron výraz, který událost spustil |
| `fired_at` | ISO timestamp okamžiku spuštění (UTC) |
| `current_time` | Čitelný formát data a dne, např. `"30. 4. 2026, 14:00, Wednesday"` |
| `prompt` | Instrukce pro agenta |

**Příklad konfigurace:**

```yaml
observers:
  - enabled: true
    type: cron
    parameters:
      interval: "0 8 * * 1-5"
    prompt: "Pošli denní shrnutí emailem"
```

---

### `dirwatch`

**Soubor:** `system/components/observers/dirwatch.py`

Sleduje adresář a reaguje na vytvoření nového souboru s danou příponou. Používá knihovnu `watchdog`.

Sledování je **nerekurzivní** — podsložky se nemonitorují.

**Parametry:**

| Parametr | Typ | Popis |
|---|---|---|
| `directory` | `str` | Absolutní cesta ke sledovanému adresáři |
| `extension` | `str` | Přípona souborů, na které reagovat, např. `"md"` nebo `".md"` |

**Publikovaná událost:** `DirWatchEvent`

| Pole | Popis |
|---|---|
| `path` | Absolutní cesta k nově vytvořenému souboru |
| `extension` | Přípona souboru (vždy s tečkou) |
| `prompt` | Instrukce pro agenta |

**Příklad konfigurace:**

```yaml
observers:
  - enabled: true
    type: dirwatch
    parameters:
      directory: "/home/user/inbox"
      extension: "md"
    prompt: "Zpracuj novou poznámku a zařaď ji do archivu"
```

---

### `filetail`

**Soubor:** `system/components/observers/filetail.py`

Sleduje soubor a reaguje na každý nový řádek — funguje analogicky k `tail -f`. Soubor je automaticky vytvořen, pokud neexistuje. Prázdné řádky jsou ignorovány.

**Parametry:**

| Parametr | Typ | Popis |
|---|---|---|
| `file` | `str` | Absolutní cesta ke sledovanému souboru |

**Publikovaná událost:** `FileEvent`

| Pole | Popis |
|---|---|
| `event` | Vždy `"new_line"` |
| `path` | Cesta ke sledovanému souboru |
| `data` | Obsah nového řádku (bez `\n`) |
| `prompt` | Instrukce pro agenta |

**Příklad konfigurace:**

```yaml
observers:
  - enabled: true
    type: filetail
    parameters:
      file: "/var/log/app/events.log"
    prompt: "Analyzuj log záznam a upozorni na chyby"
```

---

## Přidání vlastního observeru

1. Vytvoř soubor `system/components/observers/<název>.py`.
2. Definuj třídu dědící z `BaseObserver` a implementuj metodu `async def run(self, **params)`.
3. Na konci souboru přidej alias `Observer = <TvůjObserver>`.
4. Publikuj události přes `self._publish()` (async kontext) nebo `self._publish_sync()` (sync callback).

```python
from system.components.observers.base import BaseObserver
from system.models import BrokerMessage, SomeEvent

class MyObserver(BaseObserver):
    async def run(self, my_param: str):
        # logika sledování...
        await self._publish(
            BrokerMessage(type=SomeEvent.__name__, data=SomeEvent(...)),
            exchange=self.exchange,
            routing_key=self.routing_key,
        )

Observer = MyObserver
```
