---
name: comment-issue
description: Add a comment to an existing issue without changing its state (corrections, progress notes, follow-ups)
---

# Comment on an issue

## Instructions

To add a comment to an issue in the tracking system, use

```bash
.claude/skills/comment-issue/scripts/comment-issue <issue-number> --comment-file=<file>
```

The issue stays open (or closed) as it was. Use this for corrections to
an earlier report, progress notes and follow-ups; use `close-issue` when
the work is done. Never call the forge API directly for this: the shim
resolves the project's issue-scoped token, and other tokens in the
container lack issue write access.

Write a clear, self-contained comment: a reader should understand it
without the conversation that produced it.

## Examples

```bash
cat > /tmp/comment.md << 'EOF'
Correction: the failing locale is `fi` only; `sv` renders the labels.
Root cause narrowed to the fallback chain in `i18n/labels.py`.
EOF
.claude/skills/comment-issue/scripts/comment-issue 142 --comment-file=/tmp/comment.md
```