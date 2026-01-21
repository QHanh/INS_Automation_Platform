import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Moon, Sun } from 'lucide-react';
import insIcon from '../assets/icon.png';

import { getVersion } from '@tauri-apps/api/app';

export default function Layout() {
  // Theme State
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
    }
    return 'dark';
  });

  const [appVersion, setAppVersion] = useState<string>('');

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Fetch App Version
  useEffect(() => {
    async function fetchVersion() {
      try {
        const version = await getVersion();
        setAppVersion(`v${version}`);
      } catch (e) {
        console.error("Failed to get app version", e);
        setAppVersion("v0.0.0"); // Fallback
      }
    }
    fetchVersion();
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-bg-app text-text-primary">
      {/* Header */}
      <header className="p-4 bg-bg-sidebar border-b border-border-color flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-[32px] h-8 rounded-md overflow-hidden flex items-center justify-center">
            <img src={insIcon} alt="INS Logo" className="w-full h-full object-cover" />
          </div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent m-0">
            INS Automation Platform
          </h1>
        </div>

        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors text-text-secondary hover:text-text-primary"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative">
        <Outlet />
      </main>

      {/* Footer / Status Bar */}
      <FooterVersion appVersion={appVersion} />
    </div>
  );
}

function FooterVersion({ appVersion }: { appVersion: string }) {
  const [checking, setChecking] = useState(false);

  return (
    <footer className="py-1 px-4 bg-bg-sidebar border-t border-border-color text-xs text-text-tertiary flex justify-center select-none opacity-50 hover:opacity-100 transition-opacity gap-4">
      <span
        onClick={async () => {
          if (checking) return;
          setChecking(true);
          const { checkForUpdates } = await import('../services/UpdateService');
          try {
            // alert('Checking for updates...'); // Removed blocking alert
            const info = await checkForUpdates();
            if (info.error) {
              alert(`❌ Update Check Failed:\n${info.error}`);
            } else if (info.appUpdateAvailable) {
              alert(`✅ Update Available!\nNew Version: ${info.latestAppVersion}\nCurrent: ${info.currentAppVersion}\n\nPlease wait for the prompt.`);
            } else {
              alert(`✨ You are up to date.\nCurrent: ${info.currentAppVersion}\nLatest: ${info.latestAppVersion || info.currentAppVersion}`);
            }
          } catch (e) {
            alert(`❌ Error: ${e}`);
          } finally {
            setChecking(false);
          }
        }}
        className={`cursor-pointer hover:text-white hover:underline ${checking ? 'animate-pulse' : ''}`}
        title="Click to check for updates"
      >
        {checking ? 'Checking...' : `Version ${appVersion.replace('v', '')}`}
      </span>
    </footer>
  );
}
