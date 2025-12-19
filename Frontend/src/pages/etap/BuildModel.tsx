import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { etapApi } from '../../services/etapApi';
import type { EtapBuildModelRequest } from '../../services/etapApi';
import { File, Loader2, Play } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    type: 'success' | 'error' | 'info';
    message: string;
    details?: Record<string, any>;
}

const LOGS_STORAGE_KEY = 'etap-build-model-logs';

export default function ETAPBuildModel() {
    const [clsFilePath, setClsFilePath] = useState('');
    const [pcsFilePath, setPcsFilePath] = useState('');
    const [mptType, setMptType] = useState<'XFORM3W' | 'XFORM2W'>('XFORM3W');
    const [createSldElements, setCreateSldElements] = useState(true);
    const [createPoiToMptElements, setCreatePoiToMptElements] = useState(true);
    const [connectElements, setConnectElements] = useState(true);

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

    const breadcrumb = 'ETAP Tools / Build Model';

    const handleSelectClsFile = async () => {
        const selected = await selectFile([{ name: 'All Files', extensions: ['*'] }]);
        if (selected) setClsFilePath(selected);
    };

    const handleSelectPcsFile = async () => {
        const selected = await selectFile([{ name: 'All Files', extensions: ['*'] }]);
        if (selected) setPcsFilePath(selected);
    };

    const handleCreate = async (type: 'BESS' | 'PV' | 'WT') => {
        if (!clsFilePath || !pcsFilePath) {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please select both CLS and PCS files' }]);
            return;
        }

        setIsLoading(true);

        const requestData: EtapBuildModelRequest = {
            cls_file_path: clsFilePath,
            pcs_file_path: pcsFilePath,
            mpt_type: mptType,
            create_sld_elements: createSldElements,
            create_poi_to_mpt_elements: createPoiToMptElements,
            connect_elements: connectElements,
        };

        let result;
        if (type === 'BESS') {
            result = await etapApi.createBessSld(requestData);
        } else if (type === 'PV') {
            result = await etapApi.createPvSld(requestData);
        } else {
            result = await etapApi.createWtSld(requestData);
        }

        setIsLoading(false);
        const timestamp = new Date().toLocaleTimeString();

        if (result.success) {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'success',
                message: (result.data as { message?: string })?.message || `Successfully created ${type} SLD`,
                details: result.data as Record<string, any>
            }]);
        } else {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'error',
                message: result.error || `Failed to create ${type} SLD`,
                details: result.data as Record<string, any>
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
                <div className="max-w-3xl mx-auto space-y-6">
                    {/* Inputs Section */}
                    <div className="bg-bg-surface p-4 rounded-lg border border-border-color space-y-4">
                        <div className="space-y-4">
                            {/* CLS File */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-text-primary">CLS File Path</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={clsFilePath}
                                        onChange={(e) => setClsFilePath(e.target.value)}
                                        placeholder="Select CLS file..."
                                        className="flex-1 px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button onClick={handleSelectClsFile} className="px-4 py-2 bg-bg-app hover:bg-white/5 border border-border-color rounded-lg flex items-center gap-2 text-text-primary transition-colors">
                                        <File size={18} /> Browse
                                    </button>
                                </div>
                            </div>

                            {/* PCS File */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-text-primary">PCS File Path</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={pcsFilePath}
                                        onChange={(e) => setPcsFilePath(e.target.value)}
                                        placeholder="Select PCS file..."
                                        className="flex-1 px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button onClick={handleSelectPcsFile} className="px-4 py-2 bg-bg-app hover:bg-white/5 border border-border-color rounded-lg flex items-center gap-2 text-text-primary transition-colors">
                                        <File size={18} /> Browse
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* MPT Type Dropdown */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">MPT Type</label>
                            <select
                                value={mptType}
                                onChange={(e) => setMptType(e.target.value as 'XFORM3W' | 'XFORM2W')}
                                className="w-full px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
                            >
                                <option value="XFORM3W">XFORM3W (Three Winding)</option>
                                <option value="XFORM2W">XFORM2W (Two Winding)</option>
                            </select>
                        </div>

                        {/* Checkboxes */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <label className="flex items-center space-x-3 text-text-primary cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={createSldElements}
                                    onChange={(e) => setCreateSldElements(e.target.checked)}
                                    className="form-checkbox h-5 w-5 text-blue-600 rounded bg-bg-app border-border-color focus:ring-blue-500"
                                />
                                <span className="text-sm">Create SLD Elements</span>
                            </label>
                            <label className="flex items-center space-x-3 text-text-primary cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={createPoiToMptElements}
                                    onChange={(e) => setCreatePoiToMptElements(e.target.checked)}
                                    className="form-checkbox h-5 w-5 text-blue-600 rounded bg-bg-app border-border-color focus:ring-blue-500"
                                />
                                <span className="text-sm">Create POI to MPT</span>
                            </label>
                            <label className="flex items-center space-x-3 text-text-primary cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={connectElements}
                                    onChange={(e) => setConnectElements(e.target.checked)}
                                    className="form-checkbox h-5 w-5 text-blue-600 rounded bg-bg-app border-border-color focus:ring-blue-500"
                                />
                                <span className="text-sm">Connect Elements</span>
                            </label>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="grid grid-cols-3 gap-4">
                        <button
                            onClick={() => handleCreate('BESS')}
                            disabled={isLoading}
                            className="py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                            Create BESS
                        </button>
                        <button
                            onClick={() => handleCreate('PV')}
                            disabled={isLoading}
                            className="py-3 bg-green-500 hover:bg-green-600 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                            Create PV
                        </button>
                        <button
                            onClick={() => handleCreate('WT')}
                            disabled={isLoading}
                            className="py-3 bg-teal-500 hover:bg-teal-600 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                            Create WT
                        </button>
                    </div>

                    {/* Logs */}
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
                                                <span className={`font-semibold ${log.type === 'success' ? 'text-green-400' : log.type === 'error' ? 'text-red-400' : 'text-blue-400'}`}>
                                                    {log.type.toUpperCase()}:
                                                </span>
                                                <span className="text-text-primary flex-1">{log.message}</span>
                                            </div>
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
