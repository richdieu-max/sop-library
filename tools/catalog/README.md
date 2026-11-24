# Runbook tags and indexes

`build.py` writes two things from the runbooks themselves, so they cannot drift:

1. **The tag block at the top of every runbook:** status, topics, keywords, the NIST SP 800-53 Rev. 5 controls (with names) and the NIST CSF 2.0 outcomes it supports, and the other frameworks in its Control mapping table.
2. **The indexes in the top-level README:** Browse by topic, NIST SP 800-53 coverage by family, NIST CSF 2.0 coverage by function, and the NIST column in each catalog table.

| Source | Holds |
|---|---|
| Each runbook's `## Control mapping` table | The NIST SP 800-53 R5 and NIST CSF 2.0 references, and the other frameworks |
| `catalog.json` | Status, topics and keywords per runbook, and the topic names |

```bash
python3 tools/catalog/build.py           # rewrite the generated blocks
python3 tools/catalog/build.py --check   # CI: fail if anything is stale or a runbook is missing a tag
```

The check fails if a runbook has no NIST SP 800-53 or CSF 2.0 row, uses a control the script has no name for, is missing from `catalog.json`, or has fewer than 3 or more than 10 keywords. Standard library only.
