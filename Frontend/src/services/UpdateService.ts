/**
 * Update Service for INS Automation Platform
 * Handles checking for updates and installing them
 */

import { check, Update } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

// Backend API base URL
const BACKEND_URL = 'http://localhost:8123';
const GITHUB_RELEASES_API = 'https://api.github.com/repos/QHanh/INS_Automation_Platform/releases/latest';

export interface VersionInfo {
    currentAppVersion: string;
    currentBackendVersion: string;
    latestAppVersion: string | null;
    latestBackendVersion: string | null;
    appUpdateAvailable: boolean;
    backendUpdateAvailable: boolean;
    releaseNotes: string | null;
    releaseDate: string | null;
}

export interface BackendVersionResponse {
    backend_version: string;
    api_version: string;
}

export interface DownloadProgress {
    downloaded: number;
    total: number | null;
    percentage: number;
}

// Cache for update info
let cachedUpdate: Update | null = null;

/**
 * Get current backend version from the running backend
 */
export async function getBackendVersion(): Promise<BackendVersionResponse | null> {
    try {
        const response = await fetch(`${BACKEND_URL}/api/version`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Failed to get backend version:', error);
        return null;
    }
}

/**
 * Get latest release info from GitHub
 * Note: For private repos, this requires authentication token
 */
export async function getLatestGitHubRelease(): Promise<{
    version: string;
    backendVersion: string | null;
    notes: string;
    publishedAt: string;
} | null> {
    try {
        // For private repos, you'll need to add authorization header
        const response = await fetch(GITHUB_RELEASES_API, {
            headers: {
                'Accept': 'application/vnd.github.v3+json',
                // 'Authorization': 'token YOUR_GITHUB_TOKEN' // Uncomment for private repos
            }
        });

        if (response.ok) {
            const data = await response.json();

            // Parse backend version from release assets or body
            let backendVersion: string | null = null;
            const backendMatch = data.body?.match(/backend[:\s]+v?(\d+\.\d+\.\d+)/i);
            if (backendMatch) {
                backendVersion = backendMatch[1];
            }

            return {
                version: data.tag_name?.replace('v', '') || data.name,
                backendVersion,
                notes: data.body || '',
                publishedAt: data.published_at
            };
        }
        return null;
    } catch (error) {
        console.error('Failed to fetch GitHub release:', error);
        return null;
    }
}

/**
 * Check for app updates using Tauri updater
 */
export async function checkForAppUpdate(): Promise<Update | null> {
    try {
        const update = await check();
        cachedUpdate = update;
        return update;
    } catch (error) {
        console.error('Failed to check for app updates:', error);
        return null;
    }
}

/**
 * Check for all updates (app + backend)
 */
export async function checkForUpdates(): Promise<VersionInfo> {
    const [backendVersion, appUpdate] = await Promise.all([
        getBackendVersion(),
        checkForAppUpdate()
    ]);

    // Get current app version from Tauri
    const currentAppVersion = await getCurrentAppVersion();

    return {
        currentAppVersion,
        currentBackendVersion: backendVersion?.backend_version || 'Unknown',
        latestAppVersion: appUpdate?.version || null,
        latestBackendVersion: null, // Will be populated from release notes
        appUpdateAvailable: appUpdate !== null,
        backendUpdateAvailable: false, // Custom logic can be added here
        releaseNotes: appUpdate?.body || null,
        releaseDate: appUpdate?.date || null
    };
}

/**
 * Get current app version
 */
import { getVersion } from '@tauri-apps/api/app';

// ... (existing imports)

/**
 * Get current app version
 */
export async function getCurrentAppVersion(): Promise<string> {
    try {
        // This will be the version from tauri.conf.json
        return await getVersion();
    } catch {
        return '0.1.0';
    }
}

/**
 * Download and install app update
 */
export async function installAppUpdate(
    onProgress?: (progress: DownloadProgress) => void
): Promise<boolean> {
    if (!cachedUpdate) {
        const update = await checkForAppUpdate();
        if (!update) {
            console.log('No update available');
            return false;
        }
        cachedUpdate = update;
    }

    try {
        let downloaded = 0;
        let contentLength: number | null = null;

        await cachedUpdate.downloadAndInstall((event) => {
            if (event.event === 'Started') {
                contentLength = event.data.contentLength ?? null;
                console.log(`Download started: ${contentLength} bytes`);
            } else if (event.event === 'Progress') {
                downloaded += event.data.chunkLength;
                if (onProgress) {
                    onProgress({
                        downloaded,
                        total: contentLength,
                        percentage: contentLength ? Math.round((downloaded / contentLength) * 100) : 0
                    });
                }
            } else if (event.event === 'Finished') {
                console.log('Download finished');
            }
        });

        console.log('Update installed, relaunching...');
        await relaunch();
        return true;
    } catch (error) {
        console.error('Failed to install update:', error);
        throw error;
    }
}

/**
 * Compare semver versions
 * Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
 */
export function compareVersions(v1: string, v2: string): number {
    const parts1 = v1.replace('v', '').split('.').map(Number);
    const parts2 = v2.replace('v', '').split('.').map(Number);

    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const p1 = parts1[i] || 0;
        const p2 = parts2[i] || 0;
        if (p1 < p2) return -1;
        if (p1 > p2) return 1;
    }
    return 0;
}
