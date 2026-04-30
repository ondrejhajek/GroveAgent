# Skill: dokumentace

Aktualizuj dokumentaci v adresáři `docs/`.

## Pravidla

- **Pouze existující soubory** — nevytvářej nové `.md` soubory v `docs/`, pokud ti to uživatel explicitně neřekne. NIKDY neaktualizuj soubor config.yaml
- **Datum na začátku každého souboru** — na úplný začátek každého aktualizovaného souboru přidej nebo aktualizuj řádek ve tvaru:
  ```
  _Aktualizováno: YYYY-MM-DD_
  ```
- Dokumentuj **pouze to, co v kódu skutečně existuje** — žádné hypotetické funkce, parametry ani chování.
- Dokumentuj **přesně** — názvy proměnných, tříd, souborů a hodnoty limitů musí odpovídat zdrojovému kódu.
- Nepřidávej komentáře, TODOs ani vysvětlivky o budoucích plánech.
- NIKDY neaktualizuj soubor config.yaml

## Postup

1. Načti všechny existující soubory v `docs/`.
2. Načti zdrojový kód — projdi `system/` a `components/` (MCPs, tools, observers, agent.py, models.py, tasker.py, main.py).
3. Porovnej dokumentaci se zdrojovým kódem — hledej:
   - chybějící nebo zastaralé parametry a datové typy
   - chybějící sekce pro existující komponenty
   - nepřesné popisy chování (limity, výchozí hodnoty, vedlejší efekty při startu)
4. Aktualizuj pouze soubory, kde jsou skutečné rozdíly.
5. Na začátek každého upraveného souboru přidej/aktualizuj datum.

## Rozsah

Dokumentují se tyto kategorie — každá má svůj soubor:

| Soubor | Obsah |
|---|---|
| `docs/mcps.md` | Interní MCP moduly a externí MCP servery |
| `docs/tools.md` | Function tools (`system/components/tools/`) |
| `docs/observers.md` | Observers (`system/components/observers/`) |
| `docs/tools_agents.md` | Sub-agenti jako tools (sekce `tools_agents` v config.yaml) |

## Jazyk

Česky. Konzistentně s existujícím stylem souborů v `docs/`.
