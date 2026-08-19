---
name: create-enhancement
description: Create an enhancement in issue tracking system for this project
---

# Create an enhancement

## Instructions

To create an enhancement in issue tracking system for this project, use

```bash
.claude/skills/create-enhancement/scripts/create-enhancement --title="enhancement title" --prio-medium --body-file=enhancement-body.md
```

Write a clear, concise and self-containing description of the enhancement.
If there are many closely related enhancements in a single app, bundle them
into one. If you have a proposal, suggest it. Include consequences if known.
Use Markdown formatting sparingly for clarity. You can optionally prioritize
the issue with `--prio-low`, `--prio-medium` or `--prio-high`.

If issue creation is successful, the URL of the created ticket is returned
on standard output, for example:

```
https://<host>/<owner>/<repo>/issues/12
```

The last path element is the issue number (here `12`). Use the `close-issue`
skill to close it by number.

## Examples

```bash
cat > /tmp/enhancement.md << 'EOF'
### Description

reports app does not implement authorization checks.

### Proposal

Implement authorization checks similarly as in other apps.

### Consequences

Unauthorized users may access data from other tenants.
EOF

.claude/skills/create-enhancement/scripts/create-enhancement \
    --title="reports does not implement authorization checks" \
    --prio-high \
    --body-file=/tmp/enhancement.md
```