_Aktualizováno: 2026-04-30_

# MCP servery

MCP (Model Context Protocol) rozšiřují agenta o sadu nástrojů. GroveAgent podporuje dva typy MCP:

- **Interní MCP** — Python moduly v `system/components/mcps/` (nebo `components/mcps/` pro projektové přepsání), načítané přes `FastMCPToolset`
- **Externí MCP servery** — libovolný MCP server spouštěný jako podproces, konfigurovaný pod klíčem `mcpServers`

MCP `tasks` je **vždy načten automaticky**, bez ohledu na konfiguraci.

---

## Konfigurace

```yaml
agent:
  mcp:
    - <název interního mcp>

  mcpServers:
    <název>:
      command: <příkaz>
      args:
        - <arg1>
        - <arg2>
```

| Klíč | Popis |
|---|---|
| `mcp` | Seznam interních MCP modulů k načtení (bez `tasks`, ten se přidá vždy) |
| `mcpServers` | Slovník externích MCP serverů — spouštěny jako podprocesy |

---

## Interní MCP

### `tasks` _(vždy aktivní)_

**Soubor:** `system/components/mcps/tasks.py`

Správa plánovaných úloh uložených v `storage/tasks.json`. MCP je vždy načten — agent ho má k dispozici i bez explicitní konfigurace.

Každá úloha obsahuje:
- `cron` — cron výraz určující čas spuštění
- `text` — prompt, který agent spustí v daný čas
- `enabled` _(volitelné, default `true`)_ — zda se úloha má spouštět
- `id` _(volitelné)_ — unikátní identifikátor; pokud chybí, používá se `cron + text`

> **Důležité:** `storage/tasks.json` je při každém startu agenta **resetován na prázdný objekt `{}`**. Úlohy uložené přes `save_tasks` jsou dostupné pouze do příštího restartu — nepřežijí restart.

**Pracovní postup agenta:** vždy nejprve zavolat `get_tasks`, upravit seznam, poté uložit přes `save_tasks`.

**Tasker** (`system/tasker.py`) běží na pozadí v samostatném vlákně. Každou sekundu kontroluje `tasks.json` a spouští úlohy, jejichž cron výraz nastal. Při změně souboru (detekce přes mtime) automaticky přenačte seznam úloh — agent tak může za běhu přidávat nebo odstraňovat úlohy a Tasker je okamžitě respektuje.

#### Nástroje

**`get_tasks() → TasksResponse`**

Vrátí aktuální seznam naplánovaných úloh ze souboru `storage/tasks.json`.

```json
{
  "tasks": [
    { "cron": "0 8 * * 1-5", "text": "Pošli denní shrnutí" }
  ]
}
```

**`save_tasks(data: SaveTasksRequest) → SaveTasksResponse`**

Uloží celý seznam úloh jako JSON. Přepíše stávající obsah souboru.

```json
{
  "tasks": [
    { "cron": "*/30 * * * *", "text": "Zkontroluj inbox" }
  ]
}
```

---

## Externí MCP servery (`mcpServers`)

### `filesystem` _(příklad z config.yaml)_

Spouští oficiální MCP server `@modelcontextprotocol/server-filesystem`, který agentovi umožňuje číst a prohledávat soubory v zadaném adresáři.

```yaml
mcpServers:
  filesystem:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "{{STORAGE_DIR}}"
      - "/home/user/notes"
```

Jako argumenty se předávají cesty k adresářům, ke kterým má agent přístup. Podporovány jsou šablonové proměnné (viz níže).

#### Dostupné proměnné v konfiguraci

| Proměnná | Hodnota |
|---|---|
| `{{STORAGE_DIR}}` | Absolutní cesta k adresáři `storage/` v kořeni projektu |
| `{{MEMORY_FILE}}` | Absolutní cesta k `storage/MEMORY.md` |
| `{{BASE_DIR}}` | Kořenový adresář projektu |

---

## Přidání vlastního interního MCP

1. Vytvoř soubor `system/components/mcps/<název>.py` (nebo `components/mcps/<název>.py` pro projektové přepsání).
2. Definuj `FastMCP` instanci a registruj nástroje dekorátorem `@mcp.tool()`.
3. Exportuj instanci jako `mcp`.
4. Přidej `<název>` do seznamu `mcp` v `config.yaml`.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="MyMCP", instructions="Popis chování pro agenta.")

@mcp.tool()
def my_tool(param: str) -> str:
    """Popis nástroje viditelný agentem."""
    return f"výsledek: {param}"
```

```yaml
agent:
  mcp:
    - my_mcp
```
