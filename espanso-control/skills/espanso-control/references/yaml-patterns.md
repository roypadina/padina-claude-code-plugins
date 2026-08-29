# Espanso YAML Patterns

Use these patterns when editing `match/*.yml` or `config/*.yml`. Verified against Espanso's
documented match/variable syntax (Espanso 2.4.0-era docs) — the shorthand-vs-verbose distinction
below is real, not a simplification.

## Match File Shape

```yaml
matches:
  - trigger: ":hello"
    replace: "Hello world"
```

Rules:

- Keep `matches:` at top level.
- Each match is a list item under `matches`.
- Use two spaces for indentation.
- Quote triggers and replacements unless the value is a block scalar.

## Common Match Types

Simple replacement:

```yaml
- trigger: ":addr"
  replace: "123 Main Street"
```

Multi-line replacement:

```yaml
- trigger: ":sig"
  replace: |
    Best regards,
    Your Name
```

Date variable:

```yaml
- trigger: ":date"
  replace: "{{today}}"
  vars:
    - name: today
      type: date
      params:
        format: "%Y-%m-%d"
```

Date variable with an offset (e.g. tomorrow — `offset` is in seconds):

```yaml
- trigger: ":tomorrow"
  replace: "{{tomorrow}}"
  vars:
    - name: tomorrow
      type: date
      params:
        format: "%Y-%m-%d"
        offset: 86400
```

Shell variable:

```yaml
- trigger: ":uuid"
  replace: "{{id}}"
  vars:
    - name: id
      type: shell
      params:
        cmd: "uuidgen"
```

Variables can feed into each other — a shell command's output can parameterize a date format, for
example. Order matters: define the variable a later one depends on first.

## Safe Editing Checklist

1. Search for existing trigger duplicates before adding a match.
2. Preserve user comments and package directories.
3. Do not edit files under `match/packages/<name>` unless the user explicitly wants to customize a
   package — package updates will overwrite local edits there.
4. Prefer user snippets in `match/base.yml` or a new clearly named file under `match/`.
5. Restart or rely on auto-restart, then confirm daemon status with `espanso status`.
