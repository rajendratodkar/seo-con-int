# Desktop shell (Tauri)

Thin Rust shell that:

1. Spawns the Python backend sidecar (`scripts/backend/serve.py`) on `127.0.0.1:8317`.
2. Waits for the backend to accept connections (30 s timeout).
3. Opens the React frontend (Vite build) in a Tauri window.
4. Kills the backend when the window closes.

The backend publishes its per-launch token to `data/runtime/backend_token.txt`;
the `get_backend_token` Tauri command exposes it to the frontend, which sends it
as `X-Backend-Token`.

## Desktop capabilities

| Feature | How it works |
|---|---|
| **Auto-updates** | `check_updates` / `install_update` commands against the endpoint in `tauri.conf.json → tauri.updater.endpoints`. The frontend checks on startup and shows an “Install & Restart” banner. Replace the placeholder endpoint with your release server (and add a signing `pubkey` for production). |
| **Deep linking** | `sci://` scheme. The shell reads the launch argument, stores it, and emits a `deep-link` event; the frontend navigates to the matching route (`sci://drafts` → `/drafts`). Register the scheme once per machine: `scripts/desktop/register_deep_link.reg` (edit the exe path first) or via the NSIS installer. |
| **Token storage** | `keychain_set` / `keychain_get` / `keychain_delete` commands backed by the OS keychain (Windows Credential Manager). The backend token is mirrored there automatically as a fallback. |
| **Proxy & offline** | All outbound HTTP goes through `app.core.http.http_client()` which honors `SCI_HTTP_PROXY` / `SCI_HTTPS_PROXY`. The frontend shows an offline banner (`navigator.onLine`); `GET /api/diagnostics/info` reports backend-side connectivity. |
| **Crash reporting** | Frontend global error handlers → `POST /api/diagnostics/crash` → rotating backend log; forwarded to Sentry only when `SCI_SENTRY_DSN` is configured. |
| **Usage analytics** | Page views + key actions → `POST /api/diagnostics/events` → local `usage_events` table (capped at 5 000 rows). Nothing leaves the machine. |
| **Log management** | `data/runtime/backend.log` via `RotatingFileHandler` (2 MB × 3 backups). |
| **File access** | Research page supports “Open local file…” and drag-and-drop (.txt/.md/.html/.csv) → `POST /api/research/sources/from-file`; raw content archived to `data/raw/research/`. |

## Prerequisites

- Rust toolchain (`rustup`): https://rustup.rs
- Windows build tools: Microsoft C++ Build Tools + WebView2 (preinstalled on Win 11)
- Node.js (frontend) and the project Python venv (`.venv/`)

## Development

```powershell
# from the repository root
npm --prefix frontend install

# Tauri dev (starts Vite via beforeDevCommand, spawns the backend sidecar)
cd desktop/src-tauri
cargo tauri dev        # if the `tauri-cli` cargo plugin is installed
# or
cargo install tauri-cli
cargo tauri dev
```

`SCI_PROJECT_ROOT` env var can override repo-root detection (used for packaged builds).

## Production build

```powershell
cd desktop/src-tauri
cargo tauri build
```

Output: `desktop/src-tauri/target/release/bundle/nsis/`.

## Layout

```
desktop/
├── README.md
└── src-tauri/
    ├── Cargo.toml
    ├── build.rs
    ├── tauri.conf.json  # updater endpoint configured here
    ├── icons/           # icon.png (1024) + icon.ico (bundled installer)
    └── src/main.rs      # sidecar spawn + health wait + updater + deep link + keychain
```
