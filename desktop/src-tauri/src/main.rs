#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

//! Desktop shell for SEO Content Intelligence.
//!
//! Responsibilities:
//! 1. Spawn the local FastAPI backend (`scripts/backend/serve.py`) as a sidecar.
//! 2. Wait until the backend accepts connections on 127.0.0.1:8317.
//! 3. Open the React frontend and kill the backend on exit.
//! 4. Desktop extras: auto-update check on startup, `sci://` deep links,
//!    OS keychain storage for secrets.

use std::env;
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};

use serde::Serialize;
use tauri::Manager;

const BACKEND_ADDR: &str = "127.0.0.1:8317";
const BACKEND_READY_TIMEOUT_SECS: u64 = 30;
const KEYCHAIN_SERVICE: &str = "seo-content-intelligence";
const DEEP_LINK_SCHEME: &str = "sci://";

struct AppState {
    root: PathBuf,
    backend: Mutex<Option<Child>>,
    /// Deep-link URL this instance was launched with (if any).
    launch_url: Mutex<Option<String>>,
}

#[derive(Serialize)]
struct UpdateInfo {
    available: bool,
    version: Option<String>,
    notes: Option<String>,
}

/// Resolve the repository root. `SCI_PROJECT_ROOT` wins (packaged builds);
/// otherwise derive from this crate's location (`<root>/desktop/src-tauri`).
fn project_root() -> PathBuf {
    if let Ok(p) = env::var("SCI_PROJECT_ROOT") {
        return PathBuf::from(p);
    }
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .map(PathBuf::from)
        .unwrap_or_else(|| env::current_dir().unwrap_or_default())
}

/// Prefer the project virtualenv; fall back to `python` on PATH.
fn python_exe(root: &PathBuf) -> PathBuf {
    let venv = if cfg!(windows) {
        root.join(".venv").join("Scripts").join("python.exe")
    } else {
        root.join(".venv").join("bin").join("python")
    };
    if venv.exists() {
        venv
    } else {
        PathBuf::from("python")
    }
}

fn spawn_backend(root: &PathBuf) -> std::io::Result<Child> {
    let script = root.join("scripts").join("backend").join("serve.py");
    // serve.py imports `app.*`, so run from the backend directory.
    Command::new(python_exe(root))
        .arg(script)
        .current_dir(root.join("backend"))
        .spawn()
}

fn wait_for_backend(timeout: Duration) -> bool {
    let start = Instant::now();
    while start.elapsed() < timeout {
        if TcpStream::connect(BACKEND_ADDR).is_ok() {
            return true;
        }
        thread::sleep(Duration::from_millis(250));
    }
    false
}

/// The backend publishes its per-launch token to `data/runtime/backend_token.txt`.
/// Falls back to the OS keychain copy if the file is missing; a fresh token is
/// mirrored into the keychain so the frontend survives file loss.
#[tauri::command]
fn get_backend_token(state: tauri::State<'_, AppState>) -> Option<String> {
    let path = state.root.join("data").join("runtime").join("backend_token.txt");
    if let Ok(token) = std::fs::read_to_string(&path) {
        let token = token.trim().to_string();
        if !token.is_empty() {
            keychain_write("backend_token", &token);
            return Some(token);
        }
    }
    keychain_read("backend_token")
}

// -- OS keychain (Windows Credential Manager / macOS Keychain / Secret Service) --

fn keychain_write(key: &str, value: &str) -> bool {
    keyring::Entry::new(KEYCHAIN_SERVICE, key)
        .and_then(|entry| entry.set_password(value))
        .is_ok()
}

fn keychain_read(key: &str) -> Option<String> {
    keyring::Entry::new(KEYCHAIN_SERVICE, key)
        .and_then(|entry| entry.get_password())
        .ok()
}

#[tauri::command]
fn keychain_set(key: String, value: String) -> bool {
    keychain_write(&key, &value)
}

#[tauri::command]
fn keychain_get(key: String) -> Option<String> {
    keychain_read(&key)
}

#[tauri::command]
fn keychain_delete(key: String) -> bool {
    keyring::Entry::new(KEYCHAIN_SERVICE, &key)
        .and_then(|entry| entry.delete_password())
        .is_ok()
}

// -- auto-updates -------------------------------------------------------------

/// Check the configured release endpoint (tauri.conf.json → tauri.updater).
/// Never blocks the UI: the frontend calls this on startup and prompts the user.
#[tauri::command]
async fn check_updates(app: tauri::AppHandle) -> Result<UpdateInfo, String> {
    match tauri::updater::builder(app).check().await {
        Ok(update) if update.is_update_available() => Ok(UpdateInfo {
            available: true,
            // tauri 1.8 exposes no version accessor on UpdateResponse
            version: None,
            notes: update.body().cloned(),
        }),
        Ok(_) => Ok(UpdateInfo {
            available: false,
            version: None,
            notes: None,
        }),
        Err(err) => Err(err.to_string()),
    }
}

/// Download + install the update, then restart into the new version.
#[tauri::command]
async fn install_update(app: tauri::AppHandle) -> Result<bool, String> {
    let update = tauri::updater::builder(app.clone())
        .check()
        .await
        .map_err(|e| e.to_string())?;
    let available = update.is_update_available();
    if available {
        update
            .download_and_install()
            .await
            .map_err(|e| e.to_string())?;
        app.restart();
    }
    Ok(available)
}

// -- deep links ------------------------------------------------------------------

/// `sci://...` arrives as a launch argument once the scheme is registered in the OS.
fn launch_deep_link() -> Option<String> {
    env::args().find(|arg| arg.starts_with(DEEP_LINK_SCHEME))
}

#[tauri::command]
fn get_launch_url(state: tauri::State<'_, AppState>) -> Option<String> {
    state.launch_url.lock().unwrap().clone()
}

fn main() {
    let root = project_root();
    let launch_url = launch_deep_link();

    let backend = match spawn_backend(&root) {
        Ok(child) => Some(child),
        Err(err) => {
            eprintln!("failed to launch backend sidecar: {err}");
            None
        }
    };
    if backend.is_some()
        && !wait_for_backend(Duration::from_secs(BACKEND_READY_TIMEOUT_SECS))
    {
        eprintln!("backend did not become ready at {BACKEND_ADDR} in time");
    }

    let deep_link = launch_url.clone();
    let app = tauri::Builder::default()
        .manage(AppState {
            root,
            backend: Mutex::new(backend),
            launch_url: Mutex::new(launch_url),
        })
        .setup(move |app| {
            // Notify the frontend if this launch came from a sci:// link.
            if let Some(url) = deep_link {
                let _ = app.emit_all("deep-link", url);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_token,
            keychain_set,
            keychain_get,
            keychain_delete,
            check_updates,
            install_update,
            get_launch_url
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            let state = app_handle.state::<AppState>();
            let mut backend = state.backend.lock().unwrap();
            if let Some(child) = backend.as_mut() {
                let _ = child.kill();
            }
        }
    });
}
