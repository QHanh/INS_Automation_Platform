import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { psseApi, type BasicModelRequest } from '../../services/psseApi';
import { File, Loader2, Plus, Trash2 } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    type: 'success' | 'error' | 'info';
    message: string;
    details?: { logs?: string[] };
}

interface GeneratorRow {
    bus: number;
    id: string;
    reg_bus: number;
}

const LOGS_STORAGE_KEY = 'psse-logs';
const PARAMS_STORAGE_KEY = 'psse-basic-model-params';

export default function BasicModel() {
    const { selectFile } = useFileDialog();
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

    const addLog = (type: LogEntry['type'], message: string) => {
        setLogs(prev => [...prev, { timestamp: new Date().toLocaleTimeString(), type, message }]);
    };

    const loadInitialState = <T,>(key: string, defaultValue: T): T => {
        try {
            const saved = localStorage.getItem(PARAMS_STORAGE_KEY);
            if (saved) {
                const params = JSON.parse(saved);
                return (params[key] as T) ?? defaultValue;
            }
        } catch { /* ignore */ }
        return defaultValue;
    };

    // Form State
    const [savPath, setSavPath] = useState('');
    const [projectType, setProjectType] = useState<'BESS' | 'PV' | 'HYBRID'>(() => loadInitialState('projectType', 'BESS'));
    const [busFrom, setBusFrom] = useState<number | ''>(() => loadInitialState('busFrom', ''));
    const [busTo, setBusTo] = useState<number | ''>(() => loadInitialState('busTo', ''));
    const [pNet, setPNet] = useState<number | ''>(() => loadInitialState('pNet', ''));
    const [bessGens, setBessGens] = useState<GeneratorRow[]>(() => loadInitialState('bessGens', [{ bus: 0, id: '1', reg_bus: 0 }]));
    const [pvGens, setPvGens] = useState<GeneratorRow[]>(() => loadInitialState('pvGens', [{ bus: 0, id: '1', reg_bus: 0 }]));

    useEffect(() => {
        localStorage.setItem(PARAMS_STORAGE_KEY, JSON.stringify({ projectType, busFrom, busTo, pNet, bessGens, pvGens }));
    }, [projectType, busFrom, busTo, pNet, bessGens, pvGens]);

    const handleSelectFile = async () => {
        const selected = await selectFile([{ name: 'PSSE Models', extensions: ['sav'] }]);
        if (selected) setSavPath(selected);
    };

    const addGen = (type: 'BESS' | 'PV') => {
        const newRow = { bus: 0, id: '1', reg_bus: 0 };
        if (type === 'BESS') setBessGens([...bessGens, newRow]);
        else setPvGens([...pvGens, newRow]);
    };

    const updateGen = (type: 'BESS' | 'PV', index: number, field: keyof GeneratorRow, value: string | number) => {
        const setter = type === 'BESS' ? setBessGens : setPvGens;
        const current = type === 'BESS' ? [...bessGens] : [...pvGens];
        // @ts-ignore
        current[index][field] = value;
        setter(current);
    };

    const removeGen = (type: 'BESS' | 'PV', index: number) => {
        const current = type === 'BESS' ? bessGens : pvGens;
        if (current.length > 1) {
            const filtered = current.filter((_, i) => i !== index);
            if (type === 'BESS') setBessGens(filtered);
            else setPvGens(filtered);
        }
    };

    const handleRun = async () => {
        if (!savPath) { addLog('error', 'Please select SAV file'); return; }
        if (busFrom === '' || busTo === '' || pNet === '') { addLog('error', 'Please fill in all numeric fields'); return; }

        setIsLoading(true);
        addLog('info', `Starting Basic Model generation for ${projectType}...`);

        const request: BasicModelRequest = {
            sav_path: savPath,
            project_type: projectType,
            bus_from: Number(busFrom),
            bus_to: Number(busTo),
            p_net: Number(pNet),
            bess_generators: { buses: bessGens.map(g => g.bus), ids: bessGens.map(g => g.id), reg_buses: bessGens.map(g => g.reg_bus) },
            pv_generators: { buses: pvGens.map(g => g.bus), ids: pvGens.map(g => g.id), reg_buses: pvGens.map(g => g.reg_bus) }
        };

        try {
            const result = await psseApi.createBasicModel(request);
            if (result.success) addLog('success', result.data?.message || 'Completed');
            else addLog('error', result.error || result.data?.message || 'Failed');
        } catch (error: any) {
            addLog('error', error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const renderGenTable = (title: string, type: 'BESS' | 'PV', gens: GeneratorRow[]) => (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-text-primary">{title}</label>
                <button onClick={() => addGen(type)} className="p-1 text-blue-400 hover:text-blue-300 transition-colors"><Plus size={16} /></button>
            </div>
            <div className="bg-bg-surface border border-border-color rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-white/5">
                        <tr className="text-text-secondary text-xs">
                            <th className="py-2 px-3 text-left font-medium">Bus</th>
                            <th className="py-2 px-3 text-left font-medium">ID</th>
                            <th className="py-2 px-3 text-left font-medium">Reg Bus</th>
                            <th className="py-2 w-8"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border-color">
                        {gens.map((gen, idx) => (
                            <tr key={idx}>
                                <td className="py-1.5 px-2">
                                    <input type="number" value={gen.bus || ''} onChange={e => updateGen(type, idx, 'bus', parseInt(e.target.value) || 0)}
                                        className="w-full px-2 py-1 bg-bg-app border border-border-color rounded text-text-primary text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                                </td>
                                <td className="py-1.5 px-2">
                                    <input type="text" value={gen.id} onChange={e => updateGen(type, idx, 'id', e.target.value)}
                                        className="w-full px-2 py-1 bg-bg-app border border-border-color rounded text-text-primary text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                                </td>
                                <td className="py-1.5 px-2">
                                    <input type="number" value={gen.reg_bus || ''} onChange={e => updateGen(type, idx, 'reg_bus', parseInt(e.target.value) || 0)}
                                        className="w-full px-2 py-1 bg-bg-app border border-border-color rounded text-text-primary text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                                </td>
                                <td className="py-1.5 px-2 text-center">
                                    <button onClick={() => removeGen(type, idx)} disabled={gens.length <= 1}
                                        className="text-text-secondary hover:text-red-400 disabled:opacity-30 transition-colors"><Trash2 size={14} /></button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const breadcrumb = 'PSS/E Tools / Basic Model';

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border-color flex items-center gap-4">
                <BackButton />
                <h2 className="text-lg font-semibold">{breadcrumb}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-2xl mx-auto space-y-6">
                    {/* SAV File */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-text-primary">SAV File Path</label>
                        <div className="flex gap-2">
                            <input type="text" value={savPath} onChange={e => setSavPath(e.target.value)} placeholder="Select SAV file..."
                                className="flex-1 px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500" />
                            <button onClick={handleSelectFile} className="px-4 py-2 bg-bg-surface hover:bg-white/10 border border-border-color rounded-lg flex items-center gap-2">
                                <File size={18} /> Browse
                            </button>
                        </div>
                    </div>

                    {/* Project Type */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-text-primary">Project Type</label>
                        <select value={projectType} onChange={e => setProjectType(e.target.value as any)}
                            className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="BESS">BESS Alone</option>
                            <option value="PV">PV Alone</option>
                            <option value="HYBRID">Hybrid (PV + BESS)</option>
                        </select>
                    </div>

                    {/* POI & P Net */}
                    <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Bus From</label>
                            <input type="number" value={busFrom} onChange={e => setBusFrom(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">Bus To</label>
                            <input type="number" value={busTo} onChange={e => setBusTo(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-text-primary">P Net (MW)</label>
                            <input type="number" value={pNet} onChange={e => setPNet(e.target.value === '' ? '' : Number(e.target.value))}
                                className="w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                    </div>

                    {/* Generators */}
                    {(projectType === 'BESS' || projectType === 'HYBRID') && renderGenTable('BESS Generators', 'BESS', bessGens)}
                    {(projectType === 'PV' || projectType === 'HYBRID') && renderGenTable('PV Generators', 'PV', pvGens)}

                    {/* Run Button */}
                    <button onClick={handleRun} disabled={isLoading}
                        className="w-full py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2">
                        {isLoading ? <><Loader2 size={20} className="animate-spin" /> Processing...</> : 'Run Generation'}
                    </button>

                    {/* Log Box */}
                    <div className="mt-6">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm font-semibold text-text-primary">Logs</h3>
                            {logs.length > 0 && (
                                <button onClick={() => { setLogs([]); sessionStorage.removeItem(LOGS_STORAGE_KEY); }}
                                    className="text-xs text-text-secondary hover:text-text-primary transition-colors">Clear</button>
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
