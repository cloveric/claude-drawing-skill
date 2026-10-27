# Documentation layout

The skill now uses progressive disclosure:

1. Load `SKILL.md` for global rules and the compact style router.
2. Choose one style from its index.
3. Load only the linked `styles/<slug>.md` guide before writing code.
4. Consult the corresponding `lib/` module and `examples/` script only as needed.

This keeps startup context small while retaining style-specific guidance in focused documents.

Run the dependency-free consistency check with:

```bash
python3 tools/validate_style_docs.py
```
