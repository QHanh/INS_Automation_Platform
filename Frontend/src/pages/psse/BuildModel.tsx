import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { psseApi } from '../../services/psseApi';
import type { BuildModelRequest } from '../../services/psseApi';
import { File, Loader2 } from 'lucide-react';

interface LogDetails {
    sld_file?: string;
    sav_file?: string;
    raw_file?: string;
    seq_file?: string;
    message?: string;
    [key: string]: string | undefined;
}

interface LogEntry {
    timestamp: string;
    type: 'success' | 'error' | 'info';
    message: string;
    details?: LogDetails;
}

const LOGS_STORAGE_KEY = 'psse-logs';

export default function PSSEBuildModel() {
    const [filePath, setFilePath] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [logs, setLogs] = useState<LogEntry[]>(() => {
        try {
            const saved = sessionStorage.getItem(LOGS_STORAGE_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    });

    useEffect(() => {
        sessionStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(logs));
    }, [logs]);

    const { selectFile } = useFileDialog();

    const breadcrumb = 'PSS/E Tools / Build Model';

    const handleSelectFile = async () => {
        const selected = await selectFile([
            { name: 'Excel Files', extensions: ['xlsx', 'xls', 'xlsm'] },
            { name: 'CSV Files', extensions: ['csv'] },
            { name: 'All Files', extensions: ['*'] },
        ]);
        if (selected) {
            setFilePath(selected);
        }
    };

    const handleGenerate = async (type: 'equivalent' | 'detailed') => {
        if (!filePath) {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please select Calculation sheet' }]);
            return;
        }

        setIsLoading(true);

        const requestData: BuildModelRequest = {
            file_path: filePath
        };

        const result = type === 'equivalent'
            ? await psseApi.buildEquivalentModel(requestData)
            : await psseApi.buildDetailedModel(requestData);

        setIsLoading(false);

        const timestamp = new Date().toLocaleTimeString();

        if (result.success) {
            const data = result.data as LogDetails | undefined;
            setLogs(prev => [...prev, {
                timestamp,
                type: 'success',
                message: data?.message || `${type.charAt(0).toUpperCase() + type.slice(1)} model built successfully!`,
                details: data
            }]);
        } else {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'error',
                message: result.error || `Failed to generate ${type} model`
            }]);
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

                    {/* Action Buttons */}
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={() => handleGenerate('equivalent')}
                            disabled={isLoading}
                            className="py-3 bg-gradient-to-r from-blue-500 to-blue-600 
                hover:from-blue-600 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600
                text-white font-semibold rounded-lg transition-all duration-200
                flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                'Equivalent'
                            )}
                        </button>
                        <button
                            onClick={() => handleGenerate('detailed')}
                            disabled={isLoading}
                            className="py-3 bg-gradient-to-r from-purple-500 to-purple-600 
                hover:from-purple-600 hover:to-purple-700 disabled:from-gray-500 disabled:to-gray-600
                text-white font-semibold rounded-lg transition-all duration-200
                flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                'Detailed'
                            )}
                        </button>
                    </div>

                    {/* Log Box */}
                    <div className="mt-6">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm font-semibold text-text-primary">Logs</h3>
                            {logs.length > 0 && (
                                <button
                                    onClick={() => {
                                        setLogs([]);
                                        sessionStorage.removeItem(LOGS_STORAGE_KEY);
                                    }}
                                    className="text-xs text-text-secondary hover:text-text-primary transition-colors"
                                >
                                    Clear
                                </button>
                            )}
                        </div>
                        <div className="bg-bg-surface border border-border-color rounded-lg p-4 h-64 overflow-y-auto">
                            {logs.length === 0 ? (
                                <p className="text-sm text-text-secondary italic">No logs yet</p>
                            ) : (
                                <div className="space-y-2">
                                    {logs.map((log, index) => (
                                        <div key={index} className="text-sm">
                                            <div className="flex items-start gap-2">
                                                <span className="text-text-secondary text-xs font-mono">[{log.timestamp}]</span>
                                                <span className={`font-semibold ${log.type === 'success' ? 'text-green-400' :
                                                    log.type === 'error' ? 'text-red-400' :
                                                        'text-blue-400'
                                                    }`}>
                                                    {log.type.toUpperCase()}:
                                                </span>
                                                <span className="text-text-primary flex-1">{log.message}</span>
                                            </div>
                                            {log.details && (
                                                <div className="ml-20 mt-1 text-xs space-y-0.5">
                                                    {log.details.sld_file && (
                                                        <div>
                                                            <span className="text-text-secondary">SLD: </span>
                                                            <span className="text-text-primary font-mono">{log.details.sld_file}</span>
                                                        </div>
                                                    )}
                                                    {log.details.sav_file && (
                                                        <div>
                                                            <span className="text-text-secondary">SAV: </span>
                                                            <span className="text-text-primary font-mono">{log.details.sav_file}</span>
                                                        </div>
                                                    )}
                                                    {log.details.raw_file && (
                                                        <div>
                                                            <span className="text-text-secondary">RAW: </span>
                                                            <span className="text-text-primary font-mono">{log.details.raw_file}</span>
                                                        </div>
                                                    )}
                                                    {log.details.seq_file && (
                                                        <div>
                                                            <span className="text-text-secondary">SEQ: </span>
                                                            <span className="text-text-primary font-mono">{log.details.seq_file}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
