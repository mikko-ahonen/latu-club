---
name: close-issue
description: Close a bug or enhancement issue in the tracking system for this project
---

# Close a bug or enhancement

## Instructions

To close a bug or enhancement in the issue tracking system, use

```bash
.claude/skills/close-issue/scripts/close-issue <issue-number> --comment-file=<file> [--not-planned]
```

Write a clear, concise and self-containing comment explaining why the issue
was closed.

By default, the issue is closed as completed. If the issue will not be fixed
(won't fix, can't reproduce, stale), use `--not-planned`.

Refer to the issue identifier in the commit message with a hash prefix,
for example: `Fixed bug #12`.

## Examples

```bash
cat > /tmp/close.md << 'EOF'
### Problem

The reason was a syntax error in ReportListView.

### Solution

Syntax error was fixed.
EOF

.claude/skills/close-issue/scripts/close-issue 12 --comment-file=/tmp/close.md
```