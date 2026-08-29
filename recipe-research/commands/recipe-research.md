---
description: Research a dish with parallel subagents and write up a restaurant-level recipe
argument-hint: "<dish> — e.g. shakshuka, hummus, carbonara"
allowed-tools:
  - Agent
  - Read
  - Write
  - Bash
  - Glob
---

Follow the `recipe-research` skill for `$ARGUMENTS`.

No argument? Ask which dish first.

Before starting, note the plugin's configuration — output folder, vault mode, output language (the
skill's Configuration section) — and confirm the cuisine folder if none obviously fits.
