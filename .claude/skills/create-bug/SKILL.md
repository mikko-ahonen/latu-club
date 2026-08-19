---
name: create-bug
description: Create a bug in issue tracking system for this project
---

# Create a bug

## Instructions

To create a bug in issue tracking system for this project, use

```bash
.claude/skills/create-bug/scripts/create-bug --title="bug title" --prio-high --body-file=bug-body.txt
```

Write a clear, concise and self-containing description of the bug.
Include expected and observed behavior, as well as steps to produce
if known. Use Markdown formatting sparingly for clarity. You can
optionally prioritize the issue with `--prio-low`, `--prio-medium`
or `--prio-high`.

If issue creation is successful, the URL of the created ticket is
returned on standard output, for example:

```
https://<host>/<owner>/<repo>/issues/12
```

The last path element is the issue number (here `12`). Use the
`close-issue` skill to close it by number.

## Examples

```bash
cat > /tmp/bug-body.md << 'EOF'
### Observed behavior

When running fetch_url.py /reports, HTTP error 500 is returned.

### Expected behavior

HTTP error 200 is expected.

### Steps to reproduce

```bash
load_url.py /reports
```
EOF

.claude/skills/create-bug/scripts/create-bug \
    --title="Page /reports returns 500" \
    --prio-high \
    --body-file=/tmp/bug-body.md
```