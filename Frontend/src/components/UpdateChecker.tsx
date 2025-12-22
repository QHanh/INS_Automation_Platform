/**
 * UpdateChecker Component
 * Shows update notification badge and handles update installation
 */

import { useState, useEffect, useCallback } from 'react';
import {
    checkForUpdates,
    installAppUpdate,
    type VersionInfo,
    type DownloadProgress
} from '../services/UpdateService';

interface UpdateCheckerProps {
    checkInterval?: number; // in milliseconds, default 1 hour
}

type UpdateStatus = 'idle' | 'checking' | 'available' | 'downloading' | 'error';

export default function UpdateChecker({ checkInterval = 3600000 }: UpdateCheckerProps) {
    const [status, setStatus] = useState<UpdateStatus>('idle');
    const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);
    const [error, setError] = useState<string | null>(null);

    const performCheck = useCallback(async () => {
        setStatus('checking');
        setError(null);

        try {
            const info = await checkForUpdates();
            setVersionInfo(info);

            if (info.appUpdateAvailable || info.backendUpdateAvailable) {
                setStatus('available');
            } else {
                setStatus('idle');
            }
        } catch (err) {
            console.error('Update check failed:', err);
            setError(err instanceof Error ? err.message : 'Failed to check for updates');
            setStatus('error');
        }
    }, []);

    // Check for updates on mount and periodically
    useEffect(() => {
        // Initial check after 5 seconds (allow app to fully load)
        const initialTimeout = setTimeout(() => {
            performCheck();
        }, 5000);

        // Periodic check
        const interval = setInterval(performCheck, checkInterval);

        return () => {
            clearTimeout(initialTimeout);
            clearInterval(interval);
        };
    }, [performCheck, checkInterval]);

    const handleInstallUpdate = async () => {
        setStatus('downloading');
        setDownloadProgress(null);
        setError(null);

        try {
            await installAppUpdate((progress) => {
                setDownloadProgress(progress);
            });
            // App will relaunch after successful install
        } catch (err) {
            console.error('Update installation failed:', err);
            setError(err instanceof Error ? err.message : 'Failed to install update');
            setStatus('error');
        }
    };

    const handleDismiss = () => {
        setShowModal(false);
    };

    // Don't render anything if no update available
    if (status === 'idle' && !versionInfo?.appUpdateAvailable) {
        return null;
    }

    return (
        <>
            {/* Update Badge Button */}
            {status === 'available' && (
                <button
                    onClick={() => setShowModal(true)}
                    className="update-badge"
                    title="Update available"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span className="update-badge-dot" />
                </button>
            )}

            {/* Update Modal */}
            {showModal && (
                <div className="update-modal-overlay" onClick={handleDismiss}>
                    <div className="update-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="update-modal-header">
                            <h2>🚀 Update Available</h2>
                            <button className="update-modal-close" onClick={handleDismiss}>
                                ×
                            </button>
                        </div>

                        <div className="update-modal-content">
                            {versionInfo && (
                                <div className="version-info">
                                    <div className="version-row">
                                        <span className="version-label">Current Version:</span>
                                        <span className="version-value">{versionInfo.currentAppVersion}</span>
                                    </div>
                                    <div className="version-row">
                                        <span className="version-label">New Version:</span>
                                        <span className="version-value highlight">
                                            {versionInfo.latestAppVersion}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {versionInfo?.releaseNotes && (
                                <div className="release-notes">
                                    <h3>What's New:</h3>
                                    <div className="release-notes-content">
                                        {versionInfo.releaseNotes}
                                    </div>
                                </div>
                            )}

                            {status === 'downloading' && downloadProgress && (
                                <div className="download-progress">
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{ width: `${downloadProgress.percentage}%` }}
                                        />
                                    </div>
                                    <span className="progress-text">
                                        Downloading... {downloadProgress.percentage}%
                                    </span>
                                </div>
                            )}

                            {error && (
                                <div className="update-error">
                                    <span>⚠️ {error}</span>
                                </div>
                            )}
                        </div>

                        <div className="update-modal-footer">
                            <button
                                className="btn-secondary"
                                onClick={handleDismiss}
                                disabled={status === 'downloading'}
                            >
                                Remind Me Later
                            </button>
                            <button
                                className="btn-primary"
                                onClick={handleInstallUpdate}
                                disabled={status === 'downloading'}
                            >
                                {status === 'downloading' ? 'Installing...' : 'Update Now'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
        .update-badge {
          position: fixed;
          bottom: 20px;
          right: 20px;
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
          transition: transform 0.2s, box-shadow 0.2s;
          z-index: 1000;
        }

        .update-badge:hover {
          transform: scale(1.1);
          box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }

        .update-badge-dot {
          position: absolute;
          top: 0;
          right: 0;
          width: 14px;
          height: 14px;
          background: #ef4444;
          border-radius: 50%;
          border: 2px solid white;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.8; }
        }

        .update-modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1001;
        }

        .update-modal {
          background: white;
          border-radius: 16px;
          width: 90%;
          max-width: 420px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
          overflow: hidden;
        }

        .update-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .update-modal-header h2 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .update-modal-close {
          background: none;
          border: none;
          color: white;
          font-size: 24px;
          cursor: pointer;
          padding: 0;
          line-height: 1;
          opacity: 0.8;
          transition: opacity 0.2s;
        }

        .update-modal-close:hover {
          opacity: 1;
        }

        .update-modal-content {
          padding: 24px;
        }

        .version-info {
          background: #f8fafc;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 16px;
        }

        .version-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
        }

        .version-row:not(:last-child) {
          border-bottom: 1px solid #e2e8f0;
        }

        .version-label {
          color: #64748b;
          font-size: 0.875rem;
        }

        .version-value {
          font-weight: 600;
          color: #1e293b;
        }

        .version-value.highlight {
          color: #667eea;
        }

        .release-notes {
          margin-top: 16px;
        }

        .release-notes h3 {
          font-size: 0.875rem;
          color: #64748b;
          margin: 0 0 8px 0;
          font-weight: 500;
        }

        .release-notes-content {
          background: #f8fafc;
          border-radius: 8px;
          padding: 12px;
          font-size: 0.875rem;
          color: #475569;
          max-height: 150px;
          overflow-y: auto;
          white-space: pre-wrap;
        }

        .download-progress {
          margin-top: 16px;
        }

        .progress-bar {
          height: 8px;
          background: #e2e8f0;
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          transition: width 0.3s ease;
        }

        .progress-text {
          display: block;
          margin-top: 8px;
          font-size: 0.75rem;
          color: #64748b;
          text-align: center;
        }

        .update-error {
          margin-top: 16px;
          padding: 12px;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 8px;
          color: #dc2626;
          font-size: 0.875rem;
        }

        .update-modal-footer {
          display: flex;
          gap: 12px;
          padding: 16px 24px;
          background: #f8fafc;
          border-top: 1px solid #e2e8f0;
        }

        .btn-secondary, .btn-primary {
          flex: 1;
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-secondary {
          background: white;
          border: 1px solid #e2e8f0;
          color: #64748b;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #f1f5f9;
        }

        .btn-primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary:disabled, .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
          .update-modal {
            background: #1e293b;
          }

          .version-info,
          .release-notes-content {
            background: #0f172a;
          }

          .version-row:not(:last-child) {
            border-bottom-color: #334155;
          }

          .version-label {
            color: #94a3b8;
          }

          .version-value {
            color: #f1f5f9;
          }

          .release-notes-content {
            color: #cbd5e1;
          }

          .update-modal-footer {
            background: #0f172a;
            border-top-color: #334155;
          }

          .btn-secondary {
            background: #334155;
            border-color: #475569;
            color: #e2e8f0;
          }

          .btn-secondary:hover:not(:disabled) {
            background: #475569;
          }
        }
      `}</style>
        </>
    );
}
