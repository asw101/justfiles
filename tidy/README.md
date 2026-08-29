# tidy

Report and prune stale branches, worktrees and checkout directories.

```
just --justfile tidy/Justfile --list
```

## What it will and will not do

Every recipe **reports by default**. The two that can destroy anything,
`branches-prune` and `worktrees-prune`, print what they would do and exit unless you
pass `confirm=yes` as the last argument.

`dirs` and `targets` never delete. They exist to make a judgement call cheap, not to
make it for you: a scratch directory can hold the only copy of something, and no rule
can tell that from the outside.

## Recipes

| Recipe | Does |
|---|---|
| `report <repo>` | branches, worktrees and the workspace, in one pass |
| `branches <repo> [base] [remote]` | branches on `remote` already contained in `base` |
| `branches-prune <repo> [base] [remote] [confirm]` | delete them, with `confirm=yes` |
| `worktrees <repo> [base]` | worktrees, flagged clean/dirty and merged/unmerged |
| `worktrees-prune <repo> [base] [confirm]` | remove the clean and merged ones |
| `dirs` | every top-level directory in the workspace, with git state |
| `targets` | build output directories by size, largest first |

`base` defaults to `origin/main` and `remote` to `origin`. Set `TIDY_WORKSPACE` to point
`dirs` somewhere other than `~/tmp`.

## Reading the output

"Contained in `base`" means `git merge-base --is-ancestor`, so the commits are already
in the base branch and deleting the branch loses nothing. That is a stronger and more
useful test than `git branch --merged`, which only considers the current HEAD.

A fork that prepares PRs against an upstream needs both arguments, since `origin` and
the branches you want to scan are different remotes:

```
just --justfile tidy/Justfile branches ~/tmp/_components/wassette origin/main fork
```

## Two things it deliberately protects

**Branches checked out in a worktree are never proposed for deletion**, even when they
are fully merged. Deleting the remote branch under a live worktree is how you end up
with a checkout you cannot push from.

**`refs/remotes/<remote>/HEAD` abbreviates to just `<remote>`**, so a naive scan using
`%(refname:short)` yields a phantom branch named after the remote itself, and prune
would try `git push <remote> --delete <remote>`. The recipes iterate full refnames to
avoid this. It is worth knowing if you write your own version.

## Uninstalling a worktree it flags

`worktrees-prune` calls `git worktree remove`, which refuses when there are uncommitted
changes. That refusal is the point; do not reach for `--force` without looking at what
is in there.
