import React, { useState, useEffect } from 'react';
import { useFileDialog } from '../hooks/useFileDialog';
import { licenseApi } from '../services/licenseApi';
import { Lock, FileKey, AlertTriangle } from 'lucide-react';

interface LicenseGuardProps {
    children: React.ReactNode;
}

const LICENSE_STORAGE_KEY = 'ins_license_path';

export const LicenseGuard: React.FC<LicenseGuardProps> = ({ children }) => {
    const [isVerified, setIsVerified] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { selectFile } = useFileDialog();

    useEffect(() => {
        // Tự động load và verify license từ local storage khi mở app
        const checkSavedLicense = async () => {
            const savedLicensePath = localStorage.getItem(LICENSE_STORAGE_KEY);
            if (savedLicensePath) {
                try {
                    const result = await licenseApi.verifyLicense(savedLicensePath);
                    if (result.success) {
                        setIsVerified(true);
                    } else {
                        // License không hợp lệ, xóa khỏi storage
                        localStorage.removeItem(LICENSE_STORAGE_KEY);
                        setError('Saved license is invalid or expired. Please select a new license file.');
                    }
                } catch (err: any) {
                    localStorage.removeItem(LICENSE_STORAGE_KEY);
                    setError('Error loading saved license. Please select a new license file.');
                }
            }
            setLoading(false);
        };

        checkSavedLicense();
    }, []);

    const handleSelectLicense = async () => {
        setLoading(true);
        setError(null);
        try {
            const selected = await selectFile(
                [{ name: 'License Files', extensions: ['lic'] }]
            );

            if (selected) {
                const result = await licenseApi.verifyLicense(selected as string);
                if (result.success) {
                    // Lưu đường dẫn file license vào local storage
                    localStorage.setItem(LICENSE_STORAGE_KEY, selected as string);
                    setIsVerified(true);
                } else {
                    setError(result.error || 'Invalid License');
                }
            }
        } catch (err: any) {
            setError(err.message || 'Error selecting file');
        } finally {
            setLoading(false);
        }
    };

    if (isVerified) {
        return <>{children}</>;
    }

    // Hiển thị loading khi đang check license đã lưu
    if (loading) {
        return (
            <div className="fixed inset-0 z-50 bg-bg-app flex items-center justify-center">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="text-text-secondary">Checking license...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 bg-bg-app flex items-center justify-center p-4">
            <div className="bg-bg-surface border border-border-color rounded-xl shadow-2xl max-w-md w-full p-8 text-center space-y-6">
                <div className="flex justify-center mb-4">
                    <div className="p-4 bg-blue-500/10 rounded-full text-blue-400">
                        <Lock size={48} />
                    </div>
                </div>

                <h2 className="text-2xl font-bold text-text-primary">License Required</h2>
                <p className="text-text-secondary">
                    Please provide a valid license file to access the INS Automation Platform.
                </p>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 flex items-start gap-3 text-left">
                        <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={18} />
                        <span className="text-sm text-red-200">{error}</span>
                    </div>
                )}

                <button
                    onClick={handleSelectLicense}
                    disabled={loading}
                    className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <>Verifying...</>
                    ) : (
                        <>
                            <FileKey size={20} />
                            Select License File
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};
