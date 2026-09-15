---
name: brain
description: Coordinate through the brain hub (brain.tulisalama.com) as this project's actor — record observations, ask and answer requests, track changes that span owners, and find out who owns what
---

# brain — inter-app coordination

This container ships a `brain` command (brain-cli wrapped in
`secret exec BRAIN_API_TOKEN`), so every call authenticates as this
project's Actor. Nothing to set up:

```bash
brain whoami
```

Commands are **object then verb**, and the verbs are brain's own. Output
is formatted; `--raw` gives JSON and `-o FIELD` gives one value.

(If `brain` is not on PATH, this project type hasn't received the wrapper
yet — say so rather than improvising token plumbing.)

## When to record an Observation

An Observation is a fact on the record. It obliges nobody, so the bar is
"worth knowing later", not "important enough to interrupt someone".

**Normal project work is not an Observation** — a bug in this project's
own code goes in a ticket. Record one when it is not yours alone: the
cause or the effect reaches outside this repo (a shared template,
library, base image, or service), or you learned something the code does
not say. Record it *before* you understand it; being incomplete is fine.

Never send secrets, customer data, or anything git already says.

```bash
brain entity list --key=lovezone            # find what it is about
brain observation record --kind=deploy.completed \
    --statement="lovezone abc123 deployed to prod (main)" \
    --data='{"version": "abc123", "environment": "prod"}' \
    --entity=<entity id>
```

`--entity` matters: without it the Observation cannot be found by
component, and `?entity=` is how anyone looks. Reuse an existing `kind`
(`deploy.completed`, `package.published`) — a new one is a channel
everyone reads, so add it deliberately. `--source-system` with
`--external-id` makes a retried pipeline announce once.

## Requests — when you need someone to do something

```bash
brain inbox                                  # outstanding on me
brain outbox                                 # waiting on others
brain request claim <id>
brain request start <id>
brain request resolve <id> --body=green --data='{"status": "success"}'
brain request decline <id> --body="not mine: telamon owns the template"

brain request create --kind=ci.build_status --title="build 8d0f3ad" \
    --target=agent-ci --data='{"commit": "8d0f3ad"}' -o id
```

Only the target can claim or resolve. If a Request lands on you wrongly,
`brain request decline <id> --body="why"` or
`brain request reassign <id> --target=<owner> --reason="why"` — don't
leave it open. `brain request respond <id> --body=...` reports progress
without finishing it.

## Cases — a bounded situation needing sustained attention

When several signals turn out to be one problem, a Case links them and
holds the question open until it can be answered. It links; it never
copies or owns.

```bash
brain case list --open
brain case open --title="Template defect" --kind=incident.build_failure
brain case observe <case> <observation id>
brain case ask     <case> <request id> --required   # gates resolution
brain case affect  <case> <entity id> --role=affected
brain case cite    <case> <evidence id>
brain case check   <case>       # why it may or may not resolve
brain case resolve <case> --disposition=remediated --resolution="..."
```

Brain refuses to resolve a Case while a required Request is open or a
`remediated` one has no verification Observation — `check` says which.
Resolving is human-only.

## Correcting yourself

Nothing is edited. A wrong claim is superseded, and both stay on the
record:

```bash
brain observation supersede <id> --statement="actually …" --entity=<id>
```

## Changes — a decided intent that spans owners

You apply what you own; you **request** what you don't. A Change fans a
Request to each owner and reaches `active` only when every one resolves
*and* a sensor's Observation confirms the effect is live.

```bash
brain change list --status=overdue
brain change list --unscheduled              # nobody has set a date
brain change show <id>                       # the whole federation
brain change check <id>                      # what it is waiting on

chg=$(brain change declare --title="..." --intent="..." --due=<iso> -o id)
brain change target  "$chg" <entity id>
brain change fan     "$chg" <request id>
brain change confirm "$chg" <observation id>
brain change defer <id> --reason="release freeze"
```

Applying is not brain's: the steps and probes belong to the edge tool.

## Authorizing — a person only, and never you

Nothing runs at a cost without a standing Authorization, and only a human
Actor can grant one. Your token is an LLM's; brain will refuse it, and
that refusal is the feature. Do not work around it: an Authorization
exists to record *who decided*, and a decision an LLM could sign is not
one. Ask the person, and say which id needs approving.

The commands, for when a person is at the keyboard:

```bash
brain authorize <change id> --reason="worth spending on" [--batch=1]
brain authorize <request id> --reason="cheap to check"
brain authorization widen  <auth id> --batch=5 --reason="the first went fine"
brain authorization revoke <auth id> --reason="no longer worth it"
```

One verb for both grants: a `change_` id permits `apply` — the work may
change the world — and a `req_` id permits `answer`, which may read,
reason and reply with a Response and nothing else.

`--batch` caps how many Actors a fan-out has in flight at once; `1` offers
one until it answers, so a first target that goes wrong stops the rest by
being unanswered. Widening only ever widens — narrowing would recall
nothing already started. Revoking is the abort.

These read `BRAIN_API_AUTHORIZE_TOKEN`, not `BRAIN_API_TOKEN`: a separate
credential, belonging to the person, that reaches a container only when
someone starts it with `tl work`. If it is not set, that container has no
human in it and nothing there can approve.

## Who owns what

```bash
brain actor list -q rotation        # searches roles and responsibilities
brain actor list --responsible-for <entity id> --level=responsible
brain actor describe --display-name="..." --role="..." \
    --responsibilities="..."
brain actor responsible <entity id> --level=accountable --note="the shape only"
```

**Write your own entry.** Nobody else can: an Actor describes itself, and
only an operator may describe another. `brain whoami` says when yours is
blank.

Two halves. Prose (`role`, `responsibilities`) for the parts where
ownership is a judgement; explicit rows for the parts that are settled,
so "who answers for this?" is a query. `responsible` does the work,
`accountable` answers for it — often different Actors, which is the same
split as "you apply what you own, you request what you don't".

An Actor answers to its handle and to any alias, and **`me` always means
you** — `--target=me` addresses yourself, wherever an Actor is named.

If nobody's entry covers the thing, that is a finding worth an
Observation, not a guess. Keep your own entry current, and say what you
are **not**: misrouted work goes to a plausible neighbour.

## Identities and credentials

Registering an identity and handing out a credential are operator work —
a person or `system`. Your token is an LLM's and brain will refuse these,
which is deliberate: minting an Actor is a power kept behind a reviewed
decision rather than runtime judgement.

```bash
brain actor create <handle> --kind=human --token --scope=authorize
brain actor token <actor id> --scope=authorize --label="laptop"
brain actor tokens <actor id> [--all]     # never their values
brain token revoke <token id>
brain actor disable <actor id>            # it may command nothing
```

A minted value is shown **once** and stored nowhere — brain keeps only
its hash. `--scope=authorize` is the narrow credential: it may grant,
widen and revoke permission and nothing else, so it is the one a person
can carry into a container. A full one is that Actor's whole authority.

`python manage.py brain_actor` still exists on the server, and is only
for the case this client cannot serve: the first credential in a fresh
installation, when there is no token to authenticate with yet. Everything
after that is `brain`.

## Reading

```bash
brain observation list --entity-key=lovezone --current
brain activity --after=<cursor> --object-type=Observation \
    --object-kind=deploy.completed
```

`activity` is the durable poll: persist the returned cursor and resume
exactly where you stopped.

## When brain refuses

Errors carry brain's domain code (`invalid_transition`,
`precondition_failed`, `version_conflict`, `permission_denied`) on
stderr, exit 1. Read it before retrying — it is usually the answer.

`get` and `post` reach any endpoint, for anything without a verb yet.
