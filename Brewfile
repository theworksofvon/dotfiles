# Everything Homebrew installs, in one place. `brew bundle` from this
# directory installs anything missing; setup.sh calls it for you.
#
# Adding a tool is a one-line edit here — no shell script to touch.
# `brew bundle cleanup` lists installed packages this file doesn't mention.
#
# The brew/mise split: Homebrew owns tools where one global version is always
# correct. mise owns anything whose version varies per project — language
# runtimes, and the npm/pipx CLIs pinned alongside them. See mise/config.toml.
# A tool in both places means the PATH order decides which one you get, so
# each belongs in exactly one.

# ── shell ─────────────────────────────────────────
brew "starship"                  # prompt
brew "zsh-autosuggestions"       # ghosted suggestion from history
brew "zsh-syntax-highlighting"   # invalid commands turn red as you type
brew "tmux"                      # terminal multiplexer

# ── navigation and search ─────────────────────────
brew "fzf"                       # Ctrl-R fuzzy history, Ctrl-T file picker
brew "zoxide"                    # `z` jumps to frecent directories
brew "ripgrep"                   # rg
brew "fd"                        # friendlier find
brew "eza"                       # ls with git status
brew "bat"                       # cat with syntax highlighting
brew "tree"                      # directory tree

# ── development ───────────────────────────────────
brew "git"
brew "git-delta"                 # renders git diffs
brew "git-lfs"                   # gitconfig registers its filter unconditionally
brew "gh"                        # GitHub CLI; git-pr, bin/gh and auth depend on it
brew "neovim"
brew "clang-format"              # C++ formatting for the agent hook
brew "mise"                      # runtimes and CLI tools — the other half of this file
brew "jq"                        # the formatter hook parses hook payloads with it;
                                 # stays on brew so the hook never depends on a
                                 # mise shim resolving correctly
brew "cmake"                     # native build dep for several Python wheels
brew "pkgconf"                   # ditto — pkg-config for native extensions

# ── data and documents ────────────────────────────
brew "poppler"                   # pdftotext/pdfimages, used by the dev-study parsers
brew "postgresql@16"             # psql client for local dev databases
brew "sqlcmd"                    # SQL Server CLI — the Costmine backends run on MSSQL
brew "ffmpeg"                    # media transcoding
brew "yt-dlp"                    # video downloader

# ── cloud and infra ───────────────────────────────
brew "awscli"                    # AWS CLI; the RDS-to-Docker pipeline shells out to it
brew "tailscale"                 # CLI half; the cask below is the menu-bar app

# ── apps ──────────────────────────────────────────
cask "ghostty"                   # terminal
cask "t3-code"                   # editor and coding agent
cask "orbstack"                  # Docker/Linux VMs, replaces Docker Desktop
cask "tailscale-app"             # menu-bar client
cask "font-jetbrains-mono-nerd-font"   # prompt and nvim icons need a Nerd Font
cask "font-fira-code-nerd-font"        # alternate coding font

# ── deliberately NOT here ─────────────────────────
# node, bun, pnpm, uv, python, ruby  → mise (version varies per project)
# gitleaks, just, prettier, sqlfluff → mise (pinned with the projects that use them)
# nvm, fnm                           → removed; mise replaced both, and sourcing
#                                      nvm.sh cost ~230ms on every shell start
# pipx                               → removed; mise's pipx: backend runs through uv
