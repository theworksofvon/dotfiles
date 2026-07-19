# Vendored from gsong/home-directory

These two scripts are **not my work**. They come from George Song's dotfiles:
<https://github.com/gsong/home-directory> (`bin/`).

- `cc-notify.mjs` — Claude Code Stop/Notification hook. Fires a macOS
  notification only when Ghostty isn't frontmost, or when the tmux pane you're
  in isn't active — so it stays quiet while you're actually watching.
- `cc-time-left.mjs` — reads the Claude OAuth token from the macOS Keychain and
  queries Anthropic's usage endpoint to report time left in the current 5-hour
  block and the 7-day window. Caches for 5 minutes.

## Local modifications

`cc-time-left.mjs` has been changed from upstream: it now reads model-scoped
weekly limits out of the API's `limits[]` array and displays them (e.g.
`🟢Fable 2%`). Upstream reads the legacy `seven_day_opus` field, which returns
`null` on current accounts — so the model-specific quota never displayed.

## License status

**That repository has no LICENSE file.** Under default copyright that means no
redistribution right is granted, so these files are kept in `vendor/` with
attribution rather than presented as mine.

If this repo is public, resolve it properly: ask George to add a license, or
replace these with your own implementations and delete this directory.
