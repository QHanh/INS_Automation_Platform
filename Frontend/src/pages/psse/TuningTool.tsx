import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { psseApi } from '../../services/psseApi';
import type { TuningRequest } from '../../services/psseApi';
import { FolderOpen, File, Loader2 } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    type: 'success' | 'error' | 'info';
    message: string;
    details?: Record<string, unknown>;
}

const LOGS_STORAGE_KEY = 'psse-logs';
const PARAMS_STORAGE_KEY = 'psse-tuning-params';

export default function PSSETuningTool() {
    // File Paths
    const [savPath, setSavPath] = useState('');
    const [logPath, setLogPath] = useState('');

    // Helper to load initial state
    const loadInitialState = <T,>(key: string, defaultValue: T): T => {
        try {
            const saved = localStorage.getItem(PARAMS_STORAGE_KEY);
            if (saved) {
                const params = JSON.parse(saved);
                return (params[key] as T) ?? defaultValue;
            }
        } catch {
            // ignore error
        }
        return defaultValue;
    };

    // Tuning Parameters
    const [busFrom, setBusFrom] = useState<number | ''>(() => loadInitialState('busFrom', ''));
    const [busTo, setBusTo] = useState<number | ''>(() => loadInitialState('busTo', ''));
    const [genBuses, setGenBuses] = useState(() => loadInitialState('genBuses', '')); // Comma separated
    const [genIds, setGenIds] = useState(() => loadInitialState('genIds', '')); // Comma separated
    const [regBus, setRegBus] = useState(() => loadInitialState('regBus', '')); // Comma separated
    const [pTarget, setPTarget] = useState<number | ''>(() => loadInitialState('pTarget', ''));
    const [qTarget, setQTarget] = useState<number | ''>(() => loadInitialState('qTarget', ''));

    const [isLoading, setIsLoading] = useState(false);
    const [logs, setLogs] = useState<LogEntry[]>(() => {
        try {
            const saved = sessionStorage.getItem(LOGS_STORAGE_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    });

    const { selectFile, selectFolder } = useFileDialog();

    const breadcrumb = 'PSS/E Tools / Tuning Tool';

    // Save params
    useEffect(() => {
        const params = {
            busFrom,
            busTo,
            genBuses,
            genIds,
            regBus,
            pTarget,
            qTarget
        };
        localStorage.setItem(PARAMS_STORAGE_KEY, JSON.stringify(params));
    }, [busFrom, busTo, genBuses, genIds, regBus, pTarget, qTarget]);

    useEffect(() => {
        sessionStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(logs));
    }, [logs]);

    const handleSelectSavFile = async () => {
        const selected = await selectFile([
            { name: 'PSS/E Saved Case', extensions: ['sav'] },
            { name: 'All Files', extensions: ['*'] },
        ]);
        if (selected) {
            setSavPath(selected);
        }
    };

    const handleSelectLogFolder = async () => {
        const selected = await selectFolder();
        if (selected) {
            setLogPath(selected);
        }
    };

    const parseArrayInput = (input: string): string[] => {
        return input.split(',').map(s => s.trim()).filter(s => s !== '');
    };

    const handleTune = async (mode: 'P' | 'Q' | 'PQ') => {
        if (!savPath) {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please select SAV file' }]);
            return;
        }

        // Validation for numeric fields
        if (busFrom === '' || busTo === '' || pTarget === '' || qTarget === '') {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please fill in all numeric fields' }]);
            return;
        }

        setIsLoading(true);

        const requestData: TuningRequest = {
            sav_path: savPath,
            log_path: logPath || undefined,
            bus_from: Number(busFrom),
            bus_to: Number(busTo),
            gen_buses: parseArrayInput(genBuses).map(Number),
            gen_ids: parseArrayInput(genIds),
            reg_bus: parseArrayInput(regBus).map(Number),
            p_target: Number(pTarget),
            q_target: Number(qTarget),
        };

        const result = await psseApi.tuneModel(mode, requestData);

        setIsLoading(false);
        const timestamp = new Date().toLocaleTimeString();

        if (result.success) {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'success',
                message: (result.data as { message?: string })?.message || `Tuning ${mode} completed successfully`,
                details: result.data as Record<string, unknown>
            }]);
        } else {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'error',
                message: result.error || `Failed to tune ${mode}`,
                details: result.data as Record<string, unknown> // PSS/E api might return logs even on error
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
                    {/* File Inputs */}
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">SAV File Path</label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={savPath}
                                    onChange={(e) => setSavPath(e.target.value)}
                                    placeholder="Select SAV file..."
                                    className="flex-1 px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <button onClick={handleSelectSavFile} className="px-4 py-2 bg-bg-surface hover:bg-white/10 border border-border-color rounded-lg flex items-center gap-2">
                                    <File size={18} /> Browse
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Log Output Path <span className="text-text-secondary font-normal">(Optional)</span></label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={logPath}
                                    onChange={(e) => setLogPath(e.target.value)}
                                    placeholder="Select output folder..."
                                    className="flex-1 px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <button onClick={handleSelectLogFolder} className="px-4 py-2 bg-bg-surface hover:bg-white/10 border border-border-color rounded-lg flex items-center gap-2">
                                    <FolderOpen size={18} /> Browse
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Numeric Inputs */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Bus From</label>
                            <input
                                type="number"
                                value={busFrom}
                                onChange={(e) => setBusFrom(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Bus To</label>
                            <input
                                type="number"
                                value={busTo}
                                onChange={(e) => setBusTo(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* Array Inputs */}
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Gen Buses <span className="text-text-secondary font-normal">(comma separated)</span></label>
                            <input
                                type="text"
                                value={genBuses}
                                onChange={(e) => setGenBuses(e.target.value)}
                                placeholder="e.g. 101, 102, 103"
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Gen IDs <span className="text-text-secondary font-normal">(comma separated)</span></label>
                            <input
                                type="text"
                                value={genIds}
                                onChange={(e) => setGenIds(e.target.value)}
                                placeholder="e.g. 1, 1, 1"
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Regulated Buses <span className="text-text-secondary font-normal">(comma separated)</span></label>
                            <input
                                type="text"
                                value={regBus}
                                onChange={(e) => setRegBus(e.target.value)}
                                placeholder="e.g. 201, 202"
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* Target Inputs */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">P Target</label>
                            <input
                                type="number"
                                value={pTarget}
                                onChange={(e) => setPTarget(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Q Target</label>
                            <input
                                type="number"
                                value={qTarget}
                                onChange={(e) => setQTarget(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="grid grid-cols-3 gap-4 font-semibold">
                        <button
                            onClick={() => handleTune('P')}
                            disabled={isLoading}
                            className="py-3 bg-blue-500/10 border border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white rounded-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 size={18} className="animate-spin" /> : 'Tune P'}
                        </button>
                        <button
                            onClick={() => handleTune('Q')}
                            disabled={isLoading}
                            className="py-3 bg-green-500/10 border border-green-500 text-green-400 hover:bg-green-500 hover:text-white rounded-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 size={18} className="animate-spin" /> : 'Tune Q'}
                        </button>
                        <button
                            onClick={() => handleTune('PQ')}
                            disabled={isLoading}
                            className="py-3 bg-purple-500/10 border border-purple-500 text-purple-400 hover:bg-purple-500 hover:text-white rounded-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 size={18} className="animate-spin" /> : 'Tune P/Q'}
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
                                            {(log.details as { logs?: string[] })?.logs && (
                                              <div className="ml-20 mt-1 space-y-1">
                                                {Array.isArray((log.details as { logs?: string[] }).logs) && (log.details as { logs: string[] }).logs.map((l: string, i: number) => (
                                                  <div key={i} className="text-xs text-text-secondary">{l}</div>
                                                ))}
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
