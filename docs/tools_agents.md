_Aktualizováno: 2026-04-30_

# Tools agenti

Tools agenti jsou sub-agenti konfigurovaní v `config.yaml`, které hlavní agent může volat jako nástroj (tool). Každý tools agent dostane textový prompt a vrátí textovou odpověď. Hlavní agent rozhoduje, kdy a s jakým promptem sub-agenta zavolá.

---

## Konfigurace

```yaml
tools_agents:
  - enabled: true
    name: <název_nástroje>
    tool_description: <popis toolu viditelný hlavním agentem>
    model: <model id, např. openai/gpt-4o-mini>
    instructions: <systémové instrukce sub-agenta>
    parameters_doc: |
      Prompt args:
        prompt (str): Popis promptu, který sub-agent obdrží.
```

| Klíč | Popis |
|---|---|
| `enabled` | `true` / `false` — zda se tools agent načte při startu |
| `name` | Název nástroje, pod kterým ho hlavní agent vidí |
| `tool_description` | Stručný popis nástroje pro hlavního agenta (kdy a proč ho použít) |
| `model` | OpenRouter model ID použitý sub-agentem |
| `instructions` | Systémový prompt sub-agenta |
| `parameters_doc` | Dokumentace parametrů ve formátu Google docstring — popisuje `prompt` argument |

---

## Jak to funguje

Při startu agenta (`system/agent.py`) se pro každý aktivní záznam v `tools_agents` vytvoří samostatný `pydantic_ai.Agent` s daným modelem a instrukcemi. Tento agent je zaregistrován jako nástroj v `FunctionToolset` hlavního agenta.

Rozhraní nástroje:

```python
async def tools_agents_tool(prompt: str) -> str:
    result = await sub_agent.run(prompt)
    return result.output
```

Hlavní agent volá sub-agenta předáním textového promptu a obdrží textový výstup. Sub-agent nemá přístup k nástrojům ani MCP hlavního agenta — pracuje pouze se svými `instructions` a obdrženým promptem.

---

## Příklad

```yaml
tools_agents:
  - enabled: true
    name: research_agent
    tool_description: "Prohledá web a poskytne shrnutí na zadané téma"
    model: "google/gemma-3-27b-it"
    instructions: |
      Jsi výzkumný asistent. Na základě zadaného tématu poskytni stručné, faktické shrnutí.
      Odpovídej vždy v češtině.
    parameters_doc: |
      Prompt args:
        prompt (str): Téma nebo otázka, ke které má agent vyhledat informace.
```

Hlavní agent ho zavolá jako: `research_agent(prompt="Co je to pydantic-ai?")`
