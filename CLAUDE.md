# Claude instructions for latu-club

- This file is generated. Add project-specific instructions to `CLAUDE.local.md`.


latu.club — Hugo site published by GitHub Pages


## Type
Hugo



## Environments


- local - Local development environment running in Docker



## Key Operations



## Structure and files

Do not create extra directory structure. Store directories at the repository root. See README.md for organzation.

- All documentation: `docs/` directory    # For all concise, clear, documentation
- Temporary files: `tmp/` directory       # For example test reports, plans, bug fix reports


## Development Phases

In general, we work on a specific phase at the time. Phase describes the primary focus, it is informational not normative; anything can be changed at any
time and we can jump back to a phase. Phase may be related to the whole project or later iteratively for a new feature we are working on 
for existing projects.

The phases are:

concept → design → prototype → implement → testing → userguide → e2e → landing → training

There are specific instructions for each phase in `docs/claude/`. Look the corresponding instructions when doing such changes.

- `docs/claude/concept.md` -- Concept phase instructions
- `docs/claude/design.md` -- Design phase instructions
- `docs/claude/prototype.md` -- Prototyping phase instructions
- `docs/claude/implementation.md` -- Implementation and unit testing phase instructions
- `docs/claude/testing.md` -- Integration testing phase instructions
- `docs/claude/e2e.md` -- E2E testing phase instructions

## Tickets

Keep all features, todos, bugs etc. in GitHub tickets. They may be supplied by users, developers, or created by you
for example based on Sentry issues. Use the following skills instead of raw `gh` invocations — they standardize
labels and output formatting:

- `.claude/skills/list-issues/scripts/list-issues` — list open issues
- `.claude/skills/get-issue/scripts/get-issue <n>` — view issue details
- `.claude/skills/create-bug/scripts/create-bug --title=... --body-file=... [--prio-high|--prio-medium|--prio-low]` — create a bug
- `.claude/skills/create-enhancement/scripts/create-enhancement --title=... --body-file=... [--prio-*]` — create an enhancement
- `.claude/skills/close-issue/scripts/close-issue <n> --comment-file=... [--not-planned]` — close an issue

