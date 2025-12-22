use tauri::Manager;
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

struct BackendProcess {
    child: Arc<Mutex<Option<std::process::Child>>>,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            // Initialize updater plugin for desktop
            #[cfg(desktop)]
            {
                app.handle().plugin(tauri_plugin_updater::Builder::new().build())?;
                app.handle().plugin(tauri_plugin_process::init())?;
            }

            // Get the resources directory
            let resource_path = app.path().resource_dir()
                .expect("failed to get resource dir");
            
            let mut backend_path = resource_path.join("backend.exe");
            
            if !backend_path.exists() {
                #[cfg(target_os = "windows")]
                {
                    backend_path = resource_path.join("binaries").join("backend-x86_64-pc-windows-msvc.exe");
                }
                #[cfg(not(target_os = "windows"))]
                {
                     backend_path = resource_path.join("binaries").join("backend");
                }
            }
            
            println!("Attempting to spawn backend at: {:?}", backend_path);

            let mut cmd = Command::new(&backend_path);
            
            if let Some(parent) = backend_path.parent() {
                cmd.current_dir(parent);
            }

            #[cfg(target_os = "windows")]
            {
                const CREATE_NO_WINDOW: u32 = 0x08000000;
                cmd.creation_flags(CREATE_NO_WINDOW);
            }

            let child_process = match cmd
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn() {
                Ok(child) => {
                    println!("Backend process started with PID: {:?}", child.id());
                    Some(child)
                }
                Err(e) => {
                    eprintln!("Failed to spawn backend: {} at path {:?}", e, backend_path);
                    None
                }
            };

            // Manage the process state
            app.manage(BackendProcess {
                child: Arc::new(Mutex::new(child_process)),
            });

            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::ExitRequested { .. } = event {
            // Listen for the Exit event (final teardown)
            if let tauri::RunEvent::ExitRequested { .. } = event {
                let state = app_handle.state::<BackendProcess>();
                let mutex = state.child.clone();
                let lock_result = mutex.lock();
                if let Ok(mut guard) = lock_result {
                    if let Some(mut child) = guard.take() {
                        let pid = child.id();
                        println!("Killing backend process tree with PID: {}", pid);
                        
                        // Force kill the process tree on Windows
                        #[cfg(target_os = "windows")]
                        {
                            let _ = Command::new("taskkill")
                                .args(["/F", "/T", "/PID", &pid.to_string()])
                                .creation_flags(0x08000000) // CREATE_NO_WINDOW
                                .output(); // Wait for command to finish
                        }

                        // Fallback/Non-Windows standard kill
                         let _ = child.kill();
                    }
                }
            }
            }
        });
}
