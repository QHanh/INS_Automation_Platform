import { useState } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { psseApi } from '../../services/psseApi';
import { File, Loader2 } from 'lucide-react';

export default function CheckReactive() {
    const [filePath, setFilePath] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [responseData, setResponseData] = useState<any>(null);

    const { selectFile } = useFileDialog();

    const breadcrumb = 'PSS/E Tools / Check Reactive';

    const handleSelectFile = async () => {
        const selected = await selectFile([
            { name: 'Excel Files', extensions: ['xlsx', 'xls', 'xlsm'] },
            { name: 'All Files', extensions: ['*'] },
        ]);
        if (selected) {
            setFilePath(selected);
        }
    };

    const handleCheck = async () => {
        if (!filePath) {
            setError('Please select Calculation sheet');
            return;
        }

        setIsLoading(true);
        setError(null);
        setSuccess(false);
        setResponseData(null);

        const result = await psseApi.checkReactive({ file_path: filePath });

        setIsLoading(false);

        if (result.success) {
            setSuccess(true);
            setError(null);
            setResponseData(result.data);
        } else {
            setError(result.error || 'Failed to check reactive power');
            setSuccess(false);
            setResponseData(null);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border-color flex items-center gap-4">
                <BackButton />
                <h2 className="text-lg font-semibold">{breadcrumb}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-2xl mx-auto space-y-6">
                    {/* Calculation Sheet Input */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-text-primary">
                            Calculation Sheet
                        </label>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={filePath}
                                onChange={(e) => setFilePath(e.target.value)}
                                placeholder="Select or enter file path..."
                                className="flex-1 px-4 py-2 bg-bg-surface border border-border-color rounded-lg 
                  text-text-primary placeholder-text-secondary
                  focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                onClick={handleSelectFile}
                                className="px-4 py-2 bg-bg-surface hover:bg-white/10 border border-border-color 
                  rounded-lg transition-colors flex items-center gap-2"
                                title="Browse for file"
                            >
                                <File size={18} />
                                Browse
                            </button>
                        </div>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
                            {error}
                        </div>
                    )}

                    {/* Success Message */}
                    {success && responseData && (
                        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg space-y-3">
                            <div className="flex items-center gap-2 text-green-400 font-semibold">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                {responseData.message || 'Reactive power check completed successfully'}
                            </div>

                            <div className="grid gap-2 text-sm">
                                {responseData.log_file && (
                                    <div className="flex justify-between">
                                        <span className="text-text-secondary">Log File:</span>
                                        <span className="text-text-primary font-mono text-xs">{responseData.log_file}</span>
                                    </div>
                                )}
                                {responseData.error_file && (
                                    <div className="flex justify-between">
                                        <span className="text-text-secondary">Error File:</span>
                                        <span className="text-text-primary font-mono text-xs">{responseData.error_file}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Check Button */}
                    <button
                        onClick={handleCheck}
                        disabled={isLoading}
                        className="w-full py-3 bg-gradient-to-r from-blue-500 to-blue-600 
              hover:from-blue-600 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600
              text-white font-semibold rounded-lg transition-all duration-200
              flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 size={20} className="animate-spin" />
                                Checking...
                            </>
                        ) : (
                            'Check'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
