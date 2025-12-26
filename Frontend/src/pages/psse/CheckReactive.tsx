import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { psseApi, type ReactiveCheckConfig, type MptItem, type ShuntItem, type ReportPointItem } from '../../services/psseApi';
import { File, Loader2, Plus, Trash2, Save } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    type: 'success' | 'error' | 'info';
    message: string;
    details?: { logs?: string[] };
}

const LOGS_STORAGE_KEY = 'psse-logs';
const PARAMS_STORAGE_KEY = 'psse-check-reactive-params';

// Helper types for UI state
interface GeneratorRow {
    bus: number;
    id: string;
    reg_bus: number;
}

const STANDARD_REPORT_NAMES = [
    "Dummy - SUB",
    "High Side MPT1/2",
    "Low Side MPT1/2",
    "Unit at 34.5kV",
    "Unit at Gen Term"
];

const createReportPoints = (bessIndex: number) => {
    return STANDARD_REPORT_NAMES.map(name => ({
        bess_id: `GEN ${bessIndex}`,
        name: name,
        bus_from: 0,
        bus_to: 0
    }));
};

export default function CheckReactive() {
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

    // Form State
    const [savPath, setSavPath] = useState('');
    const [pNet, setPNet] = useState(() => loadInitialState('pNet', 0));
    const [busFrom, setBusFrom] = useState(() => loadInitialState('busFrom', 0));
    const [busTo, setBusTo] = useState(() => loadInitialState('busTo', 0));

    const [generators, setGenerators] = useState<GeneratorRow[]>(() =>
        loadInitialState('generators', [{ bus: 0, id: '1', reg_bus: 0 }])
    );
    const [mptList, setMptList] = useState<MptItem[]>(() =>
        loadInitialState('mptList', [{ mpt_type: '3-WINDING', mpt_from: 0, mpt_to: 0, mpt_bus_3: 0 }])
    );
    const [shuntList, setShuntList] = useState<ShuntItem[]>(() =>
        loadInitialState('shuntList', [])
    );
    const [reportPoints, setReportPoints] = useState<ReportPointItem[]>(() =>
        loadInitialState('reportPoints', createReportPoints(1))
    );

    // Save params
    useEffect(() => {
        const params = {
            pNet,
            busFrom,
            busTo,
            generators,
            mptList,
            shuntList,
            reportPoints
        };
        localStorage.setItem(PARAMS_STORAGE_KEY, JSON.stringify(params));
    }, [pNet, busFrom, busTo, generators, mptList, shuntList, reportPoints]);

    const breadcrumb = 'PSS/E Tools / Check Reactive';

    const handleSelectSav = async () => {
        const selected = await selectFile([
            { name: 'PSSE Saved Case', extensions: ['sav'] },
            { name: 'All Files', extensions: ['*'] },
        ]);
        if (selected) setSavPath(selected);
    };

    // --- Generators Handlers ---
    const addGen = () => {
        const nextIdx = generators.length + 1;
        setGenerators([...generators, { bus: 0, id: '1', reg_bus: 0 }]);
        setReportPoints([...reportPoints, ...createReportPoints(nextIdx)]);
    };
    const removeGen = (idx: number) => setGenerators(generators.filter((_, i) => i !== idx));
    const updateGen = (idx: number, field: keyof GeneratorRow, value: any) => {
        const newGens = [...generators];
        newGens[idx] = { ...newGens[idx], [field]: value };
        setGenerators(newGens);
    };

    // --- MPT Handlers ---
    const addMpt = () => setMptList([...mptList, { mpt_type: '3-WINDING', mpt_from: 0, mpt_to: 0, mpt_bus_3: 0 }]);
    const removeMpt = (idx: number) => setMptList(mptList.filter((_, i) => i !== idx));
    const updateMpt = (idx: number, field: keyof MptItem, value: any) => {
        const newList = [...mptList];
        newList[idx] = { ...newList[idx], [field]: value };
        setMptList(newList);
    };

    // --- Shunt Handlers ---
    const addShunt = () => setShuntList([...shuntList, { BUS: 0, ID: '1' }]);
    const removeShunt = (idx: number) => setShuntList(shuntList.filter((_, i) => i !== idx));
    const updateShunt = (idx: number, field: keyof ShuntItem, value: any) => {
        const newList = [...shuntList];
        newList[idx] = { ...newList[idx], [field]: value };
        setShuntList(newList);
    };

    // --- Report Points Handlers ---
    const addPoint = () => setReportPoints([...reportPoints, { bess_id: 'GEN 1', name: '', bus_from: 0, bus_to: 0 }]);

    const updatePoint = (idx: number, field: keyof ReportPointItem, value: any) => {
        const newList = [...reportPoints];
        newList[idx] = { ...newList[idx], [field]: value };
        setReportPoints(newList);
    };

    // Group points by ID
    const groupedPoints = reportPoints.reduce((acc, pt, idx) => {
        if (!acc[pt.bess_id]) acc[pt.bess_id] = [];
        acc[pt.bess_id].push({ ...pt, originalIdx: idx });
        return acc;
    }, {} as Record<string, (ReportPointItem & { originalIdx: number })[]>);


    const handleCheck = async () => {
        if (!savPath) {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please select .sav file' }]);
            return;
        }

        setIsLoading(true);

        // Transform UI state to API config
        const config: ReactiveCheckConfig = {
            SAV_PATH: savPath,
            P_NET: pNet,
            BUS_FROM: busFrom,
            BUS_TO: busTo,
            GEN_BUSES: generators.map(g => g.bus),
            GEN_IDS: generators.map(g => g.id),
            REG_BUS: generators.map(g => g.reg_bus),
            MPT_LIST: mptList,
            SHUNT_LIST: shuntList,
            REPORT_POINTS: reportPoints,
            LOG_PATH: undefined
        };

        const result = await psseApi.checkReactive(config);

        setIsLoading(false);
        const timestamp = new Date().toLocaleTimeString();

        if (result.success) {
            const data = result.data as any;
            setLogs(prev => [...prev, {
                timestamp,
                type: 'success',
                message: data?.message || 'Check Completed Successfully',
                details: { logs: data?.log }
            }]);
        } else {
            const data = result.data as any;
            setLogs(prev => [...prev, {
                timestamp,
                type: 'error',
                message: result.error || 'Check Failed',
                details: { logs: data?.log }
            }]);
        }
    };

    // Styles
    const inputClass = "w-full px-4 py-2 bg-bg-surface border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm";
    const compactInputClass = "w-full px-2 py-1 bg-bg-surface border border-border-color rounded text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm";
    const labelClass = "block text-sm font-medium text-text-primary mb-1";
    const cardClass = "space-y-4";

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border-color flex items-center gap-4">
                <BackButton />
                <h2 className="text-lg font-semibold">{breadcrumb}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-3xl mx-auto space-y-8">

                    {/* 1. Main Configuration */}
                    <div className={cardClass}>
                        <div className="space-y-2">
                            <label className={labelClass}>SAV File Path</label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={savPath}
                                    onChange={e => setSavPath(e.target.value)}
                                    className={inputClass}
                                    placeholder="Select .sav file..."
                                />
                                <button
                                    onClick={handleSelectSav}
                                    className="px-4 py-2 bg-bg-surface hover:bg-white/10 border border-border-color rounded-lg flex items-center gap-2 transition-colors"
                                >
                                    <File size={18} /> Browse
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-3">
                            <div className="space-y-2">
                                <label className={labelClass}>P Net (MW)</label>
                                <input type="number" step="0.1" value={pNet} onChange={e => setPNet(parseFloat(e.target.value) || 0)} className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className={labelClass}>Bus From (For 0.95)</label>
                                <input type="number" value={busFrom} onChange={e => setBusFrom(parseInt(e.target.value) || 0)} className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className={labelClass}>Bus To (For 0.95)</label>
                                <input type="number" value={busTo} onChange={e => setBusTo(parseInt(e.target.value) || 0)} className={inputClass} />
                            </div>
                        </div>
                    </div>

                    <hr className="border-border-color" />

                    {/* 2. Generators */}
                    <div className={cardClass}>
                        <div className="flex justify-between items-center">
                            <h3 className="text-md font-semibold text-text-primary">Generators</h3>
                            <button onClick={addGen} className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1 font-medium"><Plus size={16} /> Add Gen</button>
                        </div>

                        <div className="space-y-3">
                            {generators.map((gen, idx) => (
                                <div key={idx} className="flex gap-3 items-end bg-bg-surface/50 p-3 rounded-lg border border-border-color">
                                    <div className="flex-1">
                                        <label className="text-xs text-text-secondary mb-1 block">Gen Bus</label>
                                        <input type="number" value={gen.bus} onChange={e => updateGen(idx, 'bus', parseInt(e.target.value) || 0)} className={inputClass} />
                                    </div>
                                    <div className="w-24">
                                        <label className="text-xs text-text-secondary mb-1 block">ID</label>
                                        <input type="text" value={gen.id} onChange={e => updateGen(idx, 'id', e.target.value)} className={inputClass} />
                                    </div>
                                    <div className="flex-1">
                                        <label className="text-xs text-text-secondary mb-1 block">Reg Bus (0.95 Reactive)</label>
                                        <input type="number" value={gen.reg_bus} onChange={e => updateGen(idx, 'reg_bus', parseInt(e.target.value) || 0)} className={inputClass} />
                                    </div>
                                    <button onClick={() => removeGen(idx)} className="p-2.5 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"><Trash2 size={18} /></button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <hr className="border-border-color" />

                    {/* 3. MPT List */}
                    <div className={cardClass}>
                        <div className="flex justify-between items-center">
                            <h3 className="text-md font-semibold text-text-primary">Transformers (MPT)</h3>
                            <button onClick={addMpt} className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1 font-medium"><Plus size={16} /> Add MPT</button>
                        </div>

                        <div className="space-y-3">
                            {mptList.map((mpt, idx) => (
                                <div key={idx} className="bg-bg-surface/50 p-4 rounded-lg border border-border-color relative">
                                    <button onClick={() => removeMpt(idx)} className="absolute top-2 right-2 text-red-400 hover:text-red-300"><Trash2 size={16} /></button>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                                        <div className="space-y-1">
                                            <label className="text-xs text-text-secondary block">MPT Type</label>
                                            <select value={mpt.mpt_type} onChange={e => updateMpt(idx, 'mpt_type', e.target.value)} className={inputClass}>
                                                <option value="2-WINDING">2-Winding</option>
                                                <option value="3-WINDING">3-Winding</option>
                                            </select>
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs text-text-secondary block">From Bus (Secondary)</label>
                                            <input type="number" value={mpt.mpt_from} onChange={e => updateMpt(idx, 'mpt_from', parseInt(e.target.value) || 0)} className={inputClass} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs text-text-secondary block">To Bus (Primary)</label>
                                            <input type="number" value={mpt.mpt_to} onChange={e => updateMpt(idx, 'mpt_to', parseInt(e.target.value) || 0)} className={inputClass} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs text-text-secondary block">Tertiary Bus</label>
                                            <input
                                                type="number"
                                                value={mpt.mpt_bus_3 || 0}
                                                onChange={e => updateMpt(idx, 'mpt_bus_3', parseInt(e.target.value) || 0)}
                                                disabled={mpt.mpt_type !== '3-WINDING'}
                                                className={`${inputClass} ${mpt.mpt_type !== '3-WINDING' ? 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-800' : ''}`}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <hr className="border-border-color" />

                    {/* 4. Shunts & Report Points */}
                    <div className="grid grid-cols-1 gap-8">
                        {/* Shunts */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <h3 className="text-md font-semibold text-text-primary">Switch Shunts (Capbanks)</h3>
                                <button onClick={addShunt} className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1 font-medium"><Plus size={16} /> Add</button>
                            </div>
                            <div className="space-y-2">
                                {shuntList.map((s, idx) => (
                                    <div key={idx} className="flex gap-2 items-end p-2 bg-bg-surface/50 border border-border-color rounded-lg">
                                        <div className="flex-1">
                                            <label className="text-xs text-text-secondary mb-1 block">Bus</label>
                                            <input type="number" value={s.BUS} onChange={e => updateShunt(idx, 'BUS', parseInt(e.target.value) || 0)} className={inputClass} placeholder="Bus" />
                                        </div>
                                        <div className="flex-1">
                                            <label className="text-xs text-text-secondary mb-1 block">ID</label>
                                            <input type="text" value={s.ID} onChange={e => updateShunt(idx, 'ID', e.target.value)} className={inputClass} placeholder="ID" />
                                        </div>
                                        <button onClick={() => removeShunt(idx)} className="text-red-400 hover:text-red-300 p-2.5 bg-transparent hover:bg-white/5 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                    </div>
                                ))}
                                {shuntList.length === 0 && <div className="text-sm text-text-secondary italic">No shunts defined</div>}
                            </div>
                        </div>

                        {/* Report Points (Grouped) */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <h3 className="text-md font-semibold text-text-primary">Report Points</h3>
                                <button onClick={addPoint} className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1 font-medium"><Plus size={16} /> Add</button>
                            </div>
                            <div className="space-y-4">
                                {Object.entries(groupedPoints).map(([id, groupPoints]) => {
                                    // Handle renaming group (update bess_id for all in group)
                                    const handleGroupRename = (newId: string) => {
                                        const newPoints = [...reportPoints];
                                        groupPoints.forEach(pt => {
                                            newPoints[pt.originalIdx] = { ...newPoints[pt.originalIdx], bess_id: newId };
                                        });
                                        setReportPoints(newPoints);
                                    };

                                    // Handle deleting group
                                    const handleGroupDelete = () => {
                                        setReportPoints(reportPoints.filter(pt => pt.bess_id !== id));
                                    };

                                    return (
                                        <div key={id} className="bg-bg-surface/50 border border-border-color rounded-lg overflow-hidden">
                                            {/* Header */}
                                            <div className="bg-bg-surface border-b border-border-color px-4 py-2 flex items-center justify-between gap-2">
                                                <input
                                                    type="text"
                                                    value={id}
                                                    onChange={e => handleGroupRename(e.target.value)}
                                                    className="bg-transparent font-semibold text-sm text-text-primary focus:outline-none focus:border-b border-blue-500 flex-1"
                                                />
                                                <button onClick={handleGroupDelete} className="text-red-400 hover:text-red-300 p-1 rounded hover:bg-white/5 transition-colors" title="Delete Group">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                            {/* Table */}
                                            <div className="p-2">
                                                <div className="grid grid-cols-12 gap-2 text-xs text-text-secondary font-medium px-2 mb-1">
                                                    <div className="col-span-6">Name</div>
                                                    <div className="col-span-3">From Bus</div>
                                                    <div className="col-span-3">To Bus</div>
                                                </div>
                                                <div className="space-y-1">
                                                    {groupPoints.map((pt) => {
                                                        const idx = pt.originalIdx;
                                                        return (
                                                            <div key={idx} className="grid grid-cols-12 gap-2 items-center px-1">
                                                                <div className="col-span-6">
                                                                    <input type="text" value={pt.name} onChange={e => updatePoint(idx, 'name', e.target.value)} className={compactInputClass} />
                                                                </div>
                                                                <div className="col-span-3">
                                                                    <input type="number" value={pt.bus_from} onChange={e => updatePoint(idx, 'bus_from', parseInt(e.target.value) || 0)} className={compactInputClass} />
                                                                </div>
                                                                <div className="col-span-3">
                                                                    <input type="number" value={pt.bus_to} onChange={e => updatePoint(idx, 'bus_to', parseInt(e.target.value) || 0)} className={compactInputClass} />
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                                {reportPoints.length === 0 && <div className="text-sm text-text-secondary italic">No report points defined</div>}
                            </div>
                        </div>
                    </div>

                    {/* Action Button */}
                    <div className="pt-4">
                        <button
                            onClick={handleCheck}
                            disabled={isLoading}
                            className="w-full py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600 text-white font-semibold rounded-lg shadow-lg flex items-center justify-center gap-2 transition-all"
                        >
                            {isLoading ? <><Loader2 size={20} className="animate-spin" /> Running Analysis...</> : <><Save size={20} /> Run Reactive Check</>}
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
                                            {log.details?.logs && (
                                                <div className="ml-20 mt-1 space-y-0.5">
                                                    {log.details.logs.map((l: string, i: number) => (
                                                        <div key={i} className="text-xs text-text-secondary font-mono bg-black/20 px-1 rounded inline-block w-full">{l}</div>
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
