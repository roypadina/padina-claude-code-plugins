# recipe-research

Research a dish with three parallel subagents — classic recipes, food science, pro-chef technique —
then synthesize a restaurant-level recipe and file it into a linked note tree. Works standalone, or
wired into an Obsidian vault.

```
/plugin marketplace add roypadina/padina-claude-code-plugins
/plugin install recipe-research@padina
```

## The problem

"Find me a recipe" gets you one blogger's opinion. A restaurant-level recipe needs three things a
single search never gives you together: what several well-regarded sources actually do (and where
they disagree), the food science behind why the good version works, and what professional kitchens do
differently from home cooks. This plugin runs all three as parallel research, then makes the actual
editorial call — which disagreement resolves which way, and why — instead of averaging opinions.

## What you get

- **Three research subagents, one dispatch** — classic recipes (sourced, quantities exact), food
  science (why it works, failure modes), pro-chef technique (named chefs, restaurant practice,
  UNVERIFIED claims flagged rather than asserted).
- **A synthesized recipe**, not a copy of any one source — golden rules, metric quantities, exact
  temps/times, a "why this way" section explaining every call against the research.
- **A linked note tree**: the recipe links to three summaries, each summary links to its raw
  research. Everything is filed under `<cuisine>/<dish>/`.
- **Where the research comes from**: the subagents work from model knowledge, and search the web when
  they have those tools — the skill does not *require* a search tool, so treat "sourced" as
  attributed, not as guaranteed-live-fetched. Pro-chef claims that could not be pinned to a named
  chef or restaurant are flagged `UNVERIFIED` rather than asserted.
- **Obsidian optional.** Off by default: plain relative Markdown links, readable in any editor or on
  GitHub. Turn it on and the same structure gets `[[wiki-links]]` and frontmatter tags instead.

## Configuration

Three options — `/plugin configure recipe-research`, or set them at install:

```
/plugin install recipe-research@padina --config outputDir=~/recipes --config vaultMode=true --config language=english
```

| Option | Type | Default | |
|---|---|---|---|
| `outputDir` | directory | `~/recipes` | Where dish folders are written |
| `vaultMode` | boolean | `false` | `true` for Obsidian `[[wiki-links]]` + frontmatter tags; `false` for plain relative Markdown links |
| `language` | string | `auto` | Language for the recipe and summaries. `auto` matches whatever language you're writing in |

Nothing configured? You get `~/recipes`, plain mode, and your own language — the safe assumption is
that you are not necessarily running Obsidian.

### Turning on vault mode

If you keep an Obsidian vault, point `outputDir` at (a subfolder of) it and set `vaultMode=true`. The
plugin then writes `[[wiki-links]]` instead of relative paths and adds `tags`/`source-agent`/`date`
frontmatter to raw files — Obsidian's graph view and tag search pick the note tree up natively.
Everything else about the workflow is identical.

## Usage

```
/recipe-research shakshuka
```

Or just ask: "research a recipe for hummus", "find me a restaurant-level carbonara", "add shakshuka
to my recipes".

## Output structure

```
<outputDir>/<cuisine>/<dish>/
  <dish>.md                     # synthesized recipe — the hub
  research/
    classic-recipes.md          # summary: recipes compared
    food-science.md             # summary: why it works
    pro-technique.md            # summary: pro/restaurant technique
    raw/
      classic-recipes-raw.md    # verbatim subagent output
      food-science-raw.md
      pro-technique-raw.md
```

## Layout

```
.claude-plugin/plugin.json
commands/recipe-research.md       the /recipe-research slash command
skills/recipe-research/SKILL.md   the full workflow, for Claude
```

## License

MIT © Roy Padina
