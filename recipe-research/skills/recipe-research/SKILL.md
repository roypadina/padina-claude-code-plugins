---
name: recipe-research
description: Use when asked to research a recipe, find "the best" version of a dish, create a restaurant-level recipe, or add a dish to a recipe collection — e.g. "research a recipe for X", "find me a hummus recipe like a restaurant", "add X to my recipes", "/recipe-research X".
---

# Recipe Research

Research a dish with parallel subagents, synthesize a restaurant-level recipe, and file it into a linked note tree — with or without Obsidian.

## Configuration

Three options, set via `/plugin configure recipe-research` or at install (`--config key=value`). Stored in `settings.json` under `pluginConfigs["recipe-research"]` — check `~/.claude/settings.json` (user scope) or the project's `.claude/settings.json` / `.claude/settings.local.json` (project/local scope) if you need to read what's configured.

| Key | Type | Default | Meaning |
|---|---|---|---|
| `outputDir` | directory | `~/recipes` | Where dish folders get written |
| `vaultMode` | boolean | `false` | `true` = Obsidian `[[wiki-links]]` + frontmatter tags. `false` (default) = plain relative Markdown links, readable anywhere |
| `language` | string | `auto` | Language for the synthesized recipe and summaries. `auto` = match the language the user is writing in |

Nothing ever configured? Use the defaults above — plain mode, `~/recipes`, the user's own language. Don't assume vault mode; the safe default is that no Obsidian vault exists.

## Output structure (per dish)

```
<outputDir>/<cuisine>/<dish-slug>/
  <dish-slug>.md                # final synthesized recipe — the hub
  research/
    classic-recipes.md          # summary: recipes compared, consensus vs disagreements
    food-science.md              # summary: why it works
    pro-technique.md            # summary: pro/restaurant technique
    raw/
      classic-recipes-raw.md    # verbatim agent output
      food-science-raw.md
      pro-technique-raw.md
```

- `<cuisine>` — existing folder if one fits; otherwise ask which cuisine folder, offer to create one.
- `<dish-slug>` — lowercase-kebab-case of the dish name (`hummus`, `shakshuka`) — safe on every filesystem regardless of output language.
- **Vault mode:** every file links onward via `[[wiki-links]]` in a quoted header block; raw files get frontmatter (`tags`, `source-agent`, `date`).
- **Plain mode:** same links, as relative Markdown — `[Classic recipes](./research/classic-recipes.md)`, `[Raw](./raw/classic-recipes-raw.md)` — no frontmatter tags needed, a plain `# Title` heading is enough.

## Workflow

1. **Fan out 3 research subagents in ONE message** (general-purpose, background). Pick per-agent models to match effort — the two survey agents below don't need your strongest model; reserve that for pro-chef technique, where evidence is thinner and synthesis matters more. (One model tier for all three is fine if that's all you have access to.)
   - **Classic recipes:** 4–6 highly-regarded recipes (named sources), exact quantities, soak/rest/cook times, temps, method details, yield, serving. End with CONSENSUS vs DISAGREEMENTS.
   - **Food science:** why the restaurant version works — binding/texture/temperature chemistry, failure modes + causes + fixes, numbers (°C, grams, minutes), make-ahead/storage. Cite sources.
   - **Pro-chef technique:** what acclaimed chefs and famous restaurants for this dish do differently — named chefs, published recipes, regional truth, pro-vs-home contradictions, serving system. Flag UNVERIFIED claims explicitly.
   - Every prompt starts: "Research task, return raw data (your final text is data for synthesis, not user-facing prose)."
2. **While waiting:** create the folder tree (`mkdir -p <outputDir>/<cuisine>/<dish-slug>/research/raw`).
3. **As each agent lands:** save its output verbatim to the matching `raw/` file (each source agent's own working language — usually English, since most cooking literature is English), then write the summary note in the configured output language — condensed slightly, all numbers/sources/quotes preserved, technical terms and source names kept in their original language.
4. **After all 3 land — synthesize the recipe (main thread, no extra agent):** resolve the disagreements with the science + pro evidence and say why. Recipe format:
   - frontmatter (vault mode) or a plain header block (plain mode): tags/level/servings/prep-time/total-time
   - 3–4 load-bearing golden rules
   - ingredient tables (metric), grouped
   - numbered steps in clear prose — temps/times exact; critical-order sequences flagged with a bold warning line
   - "why this way" — decisions vs the research
   - storage/make-ahead; evidence-backed variations
5. **Report back:** file list + the 3–4 golden principles.

## Rules

- Recipe + summaries in the configured language; raw files stay in each source agent's own working language. If the user writes in another language mid-task, match it.
- Never assert claims the pro-technique agent flagged UNVERIFIED — carry the flag into the summary.
- This is a research task with a file deliverable, not a web page — write to the configured output folder; don't publish it as a web artifact.
- Existing dish folder? Update files in place, don't duplicate.

## Common mistakes

- Synthesizing before all agents return — the pro-technique agent usually overturns home-recipe defaults (temperature, leavening, timing).
- Writing summaries without back-links — every note must link to its recipe and its raw file.
- Converting to cups/imperial — keep metric + °C primary.
- Assuming vault mode when it isn't configured — default is plain mode; check before using `[[wiki-links]]`.
