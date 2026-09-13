# Writing a changelog entry

Reached from the Changelogs pointer in `AGENTS.md`. Applies when the repo
already has a `CHANGELOG.md`. Never create one where it doesn't exist.

## The file's own history is the spec

Read the existing entries before writing anything, and copy that file's
conventions exactly:

- heading style
- version and date format
- section names — `Added`/`Fixed`/`Changed`, or something bespoke
- bullet phrasing and tense
- whether entries link to PRs or issues

Not Keep a Changelog, and not any other project's habits. If the file does
something unusual and consistent, that is the convention.

## What to write

Describe the change as shipped, not the process of getting there. Write what a
user of this project would notice.

Good: `Fixed hauler strip routines charging operator cost when tonnage is zero.`

Bad: `Refactored the strip cost calculation and added a guard clause.` — that
is the diff, not the change.

## Where it goes

Add to the unreleased or in-progress section if the file has one. Don't invent
a version number or a release date; releasing is a separate act.

If there is no unreleased section and the file groups strictly by released
version, say so and ask rather than opening a new version heading.
