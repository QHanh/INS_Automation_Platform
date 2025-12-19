import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { pscadApi } from '../../services/pscadApi';
import type { ConvertSimulinkRequest } from '../../services/pscadApi';
import { FolderOpen, Loader2, Play } from 'lucide-react';

interface LogDetails {
    output_file?: string;
    message?: string;
    [key: string]: string | undefined;
}

interface LogEntry {
    timestamp: string;
    type: 'success' | 'error' | 'info';
    message: string;
    details?: LogDetails;
}

const LOGS_STORAGE_KEY = 'pscad-logs';

export default function PSCADConvertSimulink() {
    const [simulinkFolder, setSimulinkFolder] = useState('');
    const [outputPath, setOutputPath] = useState('');
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

    const { selectFolder } = useFileDialog();

    const breadcrumb = 'PSCAD Tools / Convert Simulink to PSCAD';

    const handleSelectSimulinkFolder = async () => {
        const selected = await selectFolder();
        if (selected) setSimulinkFolder(selected);
    };

    const handleSelectOutputPath = async () => {
        const selected = await selectFolder();
        if (selected) setOutputPath(selected);
    };

    const handleGenerate = async () => {
        if (!simulinkFolder) {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please select Simulink Folder' }]);
            return;
        }

        setIsLoading(true);

        const requestData: ConvertSimulinkRequest = {
            simulink_folder: simulinkFolder,
            output_path: outputPath || undefined,
        };

        const result = await pscadApi.convertSimulink(requestData);

        setIsLoading(false);
        const timestamp = new Date().toLocaleTimeString();

        if (result.success) {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'success',
                message: (result.data as { message?: string })?.message || 'Conversion simulink to pscad successful',
                details: result.data as LogDetails
            }]);
        } else {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'error',
                message: result.error || 'Failed to convert Simulink model',
                details: result.data as LogDetails
            }]);
        }
    };

    return (
        <div className="flex flex-col h-full bg-bg-app">
            <div className="p-4 border-b border-border-color flex items-center gap-4 bg-bg-surface">
                <BackButton />
                <h2 className="text-lg font-semibold text-text-primary">{breadcrumb}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-border-color scrollbar-track-transparent">
                <div className="max-w-2xl mx-auto space-y-6">
                    {/* Inputs Section */}
                    <div className="bg-bg-surface p-4 rounded-lg border border-border-color space-y-4">
                        <div className="space-y-4">
                            {/* Simulink Folder */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-text-primary">Simulink Folder</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={simulinkFolder}
                                        onChange={(e) => setSimulinkFolder(e.target.value)}
                                        placeholder="Select folder containing Simulink model..."
                                        className="flex-1 px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button onClick={handleSelectSimulinkFolder} className="px-4 py-2 bg-bg-app hover:bg-white/5 border border-border-color rounded-lg flex items-center gap-2 text-text-primary transition-colors">
                                        <FolderOpen size={18} /> Browse
                                    </button>
                                </div>
                            </div>

                            {/* Output Path */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-text-primary">
                                    Output Path <span className="text-text-secondary font-normal">(Optional)</span>
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={outputPath}
                                        onChange={(e) => setOutputPath(e.target.value)}
                                        placeholder="Select output folder..."
                                        className="flex-1 px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button onClick={handleSelectOutputPath} className="px-4 py-2 bg-bg-app hover:bg-white/5 border border-border-color rounded-lg flex items-center gap-2 text-text-primary transition-colors">
                                        <FolderOpen size={18} /> Browse
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Generate Button */}
                    <button
                        onClick={handleGenerate}
                        disabled={isLoading}
                        className="w-full py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                        {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                        Generate
                    </button>

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
                                            {log.details?.output_file && (
                                                <div className="ml-20 mt-1 text-xs">
                                                    <span className="text-text-secondary">Output: </span>
                                                    <span className="text-text-primary font-mono">{log.details.output_file}</span>
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
