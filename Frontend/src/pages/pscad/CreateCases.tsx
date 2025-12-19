import { useState, useEffect } from 'react';
import BackButton from '../../components/BackButton';
import { useFileDialog } from '../../hooks/useFileDialog';
import { pscadApi } from '../../services/pscadApi';
import type { CreateCasesRequest, PSCADCase } from '../../services/pscadApi';
import { FolderOpen, File, Loader2, Plus, Trash2, X, Pencil, ChevronDown, ChevronRight } from 'lucide-react';

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
const PARAMS_STORAGE_KEY = 'pscad-create-cases-params-v3';

export default function PSCADCreateCases() {
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

    const [projectPath, setProjectPath] = useState(() => loadInitialState('projectPath', ''));
    const [originalFilename, setOriginalFilename] = useState(() => loadInitialState('originalFilename', ''));

    const [isLoading, setIsLoading] = useState(false);
    const [logs, setLogs] = useState<LogEntry[]>(() => {
        try {
            const saved = sessionStorage.getItem(LOGS_STORAGE_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    });

    const breadcrumb = 'PSCAD Tools / Setup Case';

    useEffect(() => {
        sessionStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(logs));
    }, [logs]);

    interface UICase {
        new_filename: string;
        components: UIComponent[];
        isEditingName?: boolean;
        isCollapsed?: boolean;
    }
    interface UIComponent {
        id: number;
        parametersList: { key: string; value: string }[];
    }

    const { selectFile, selectFolder } = useFileDialog();

    const [uiCases, setUiCases] = useState<UICase[]>(() => loadInitialState('uiCases', [
        { new_filename: 'case1.pscx', components: [{ id: 0, parametersList: [{ key: '', value: '' }] }], isCollapsed: false }
    ]));
    useEffect(() => {
        const params = {
            projectPath,
            originalFilename,
            uiCases
        };
        localStorage.setItem(PARAMS_STORAGE_KEY, JSON.stringify(params));
    }, [projectPath, originalFilename, uiCases]);

    const addUiCase = () => {
        const nextCaseNum = uiCases.length + 1;
        setUiCases([...uiCases, {
            new_filename: `case${nextCaseNum}.pscx`,
            components: [{ id: 0, parametersList: [{ key: '', value: '' }] }],
            isCollapsed: false
        }]);
    };

    const removeUiCase = (index: number) => {
        const newCases = [...uiCases];
        newCases.splice(index, 1);
        setUiCases(newCases);
    };

    const updateUiCaseFilename = (index: number, value: string) => {
        const newCases = [...uiCases];
        newCases[index].new_filename = value;
        setUiCases(newCases);
    };

    const toggleCaseNameEdit = (index: number) => {
        const newCases = [...uiCases];
        newCases[index].isEditingName = !newCases[index].isEditingName;
        setUiCases(newCases);
    };

    const toggleCollapse = (index: number) => {
        const newCases = [...uiCases];
        newCases[index].isCollapsed = !newCases[index].isCollapsed;
        setUiCases(newCases);
    };

    const addUiComponent = (caseIndex: number) => {
        const newCases = [...uiCases];
        newCases[caseIndex].components.push({ id: 0, parametersList: [{ key: '', value: '' }] });
        setUiCases(newCases);
    };

    const removeUiComponent = (caseIndex: number, compIndex: number) => {
        const newCases = [...uiCases];
        newCases[caseIndex].components.splice(compIndex, 1);
        setUiCases(newCases);
    };

    const updateUiComponentId = (caseIndex: number, compIndex: number, value: string) => {
        const newCases = [...uiCases];
        newCases[caseIndex].components[compIndex].id = Number(value);
        setUiCases(newCases);
    };

    const addUiParameter = (caseIndex: number, compIndex: number) => {
        const newCases = [...uiCases];
        newCases[caseIndex].components[compIndex].parametersList.push({ key: '', value: '' });
        setUiCases(newCases);
    };

    const removeUiParameter = (caseIndex: number, compIndex: number, paramIndex: number) => {
        const newCases = [...uiCases];
        newCases[caseIndex].components[compIndex].parametersList.splice(paramIndex, 1);
        setUiCases(newCases);
    };

    const updateUiParameter = (caseIndex: number, compIndex: number, paramIndex: number, field: 'key' | 'value', value: string) => {
        const newCases = [...uiCases];
        newCases[caseIndex].components[compIndex].parametersList[paramIndex][field] = value;
        setUiCases(newCases);
    };

    const handleSelectProjectPath = async () => {
        const selected = await selectFolder();
        if (selected) setProjectPath(selected);
    };

    const handleSelectOriginalFile = async () => {
        const selected = await selectFile([{ name: 'PSCAD File', extensions: ['pscx'] }, { name: 'All Files', extensions: ['*'] }]);
        if (selected) {
            const name = selected.split(/\\|\//).pop() || '';
            setOriginalFilename(name);
        }
    };

    const handleCreateCases = async () => {
        if (!projectPath || !originalFilename) {
            const timestamp = new Date().toLocaleTimeString();
            setLogs(prev => [...prev, { timestamp, type: 'error', message: 'Please select Project Path and Original Filename' }]);
            return;
        }

        setIsLoading(true);

        const apiCases: PSCADCase[] = uiCases.map(c => ({
            new_filename: c.new_filename,
            components: c.components.map(comp => {
                const paramsObj: Record<string, any> = {};
                comp.parametersList.forEach(p => {
                    if (p.key.trim()) {
                        const numVal = Number(p.value);
                        paramsObj[p.key] = isNaN(numVal) || p.value.trim() === '' ? p.value : numVal;
                    }
                });
                return {
                    id: comp.id,
                    parameters: paramsObj
                };
            })
        }));

        const requestData: CreateCasesRequest = {
            project_path: projectPath,
            original_filename: originalFilename,
            cases: apiCases
        };

        const result = await pscadApi.createCases(requestData);

        setIsLoading(false);
        const timestamp = new Date().toLocaleTimeString();

        if (result.success) {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'success',
                message: (result.data as { message?: string })?.message || 'Batch creation completed',
                details: result.data as LogDetails
            }]);
        } else {
            setLogs(prev => [...prev, {
                timestamp,
                type: 'error',
                message: result.error || 'Failed to create cases',
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
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* Top Section: Common Inputs */}
                    <div className="bg-bg-surface p-4 rounded-lg border border-border-color space-y-4">
                        <div className="grid gap-4">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-text-primary">Project Path</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={projectPath}
                                        onChange={(e) => setProjectPath(e.target.value)}
                                        placeholder="Select project folder..."
                                        className="flex-1 px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button onClick={handleSelectProjectPath} className="px-4 py-2 bg-bg-app hover:bg-white/5 border border-border-color rounded-lg flex items-center gap-2 text-text-primary transition-colors">
                                        <FolderOpen size={18} /> Browse
                                    </button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-text-primary">Original Filename</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={originalFilename}
                                        onChange={(e) => setOriginalFilename(e.target.value)}
                                        placeholder="e.g. main.pscx"
                                        className="flex-1 px-4 py-2 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button onClick={handleSelectOriginalFile} className="px-4 py-2 bg-bg-app hover:bg-white/5 border border-border-color rounded-lg flex items-center gap-2 text-text-primary transition-colors">
                                        <File size={18} /> Browse
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Dynamic Cases List */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-md font-semibold text-text-primary">Cases</h3>
                            <button onClick={addUiCase} className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white rounded-md transition-all text-sm font-medium border border-blue-500/50">
                                <Plus size={16} /> Add Case
                            </button>
                        </div>

                        {uiCases.map((uiCase, caseIdx) => (
                            <div key={caseIdx} className="bg-bg-surface p-4 rounded-lg border border-border-color relative group">
                                <button
                                    onClick={() => removeUiCase(caseIdx)}
                                    className="absolute top-4 right-4 text-text-secondary hover:text-red-400 p-1 rounded-md hover:bg-red-400/10 transition-colors"
                                    title="Remove Case"
                                >
                                    <Trash2 size={18} />
                                </button>

                                <div className="space-y-4">
                                    <div className="flex items-center gap-2 pr-10">
                                        <button onClick={() => toggleCollapse(caseIdx)} className="text-text-secondary hover:text-text-primary">
                                            {uiCase.isCollapsed ? <ChevronRight size={18} /> : <ChevronDown size={18} />}
                                        </button>
                                        {uiCase.isEditingName ? (
                                            <input
                                                type="text"
                                                value={uiCase.new_filename}
                                                onChange={(e) => updateUiCaseFilename(caseIdx, e.target.value)}
                                                onBlur={() => toggleCaseNameEdit(caseIdx)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') toggleCaseNameEdit(caseIdx);
                                                }}
                                                placeholder="e.g. mainLVRT.pscx"
                                                autoFocus
                                                className="px-2 py-1 bg-bg-app border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
                                            />
                                        ) : (
                                            <div className="flex items-center gap-2 group/edit">
                                                <span className="text-text-primary font-semibold">{uiCase.new_filename || 'Untitled Case'}</span>
                                                <button
                                                    onClick={() => toggleCaseNameEdit(caseIdx)}
                                                    className="text-text-secondary hover:text-blue-400 transition-all p-1"
                                                >
                                                    <Pencil size={14} />
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    {/* Components List */}
                                    {!uiCase.isCollapsed && (
                                        <div className="space-y-4">
                                            {uiCase.components.map((comp, compIdx) => (
                                                <div key={compIdx} className="bg-bg-app/50 p-3 pr-8 rounded-md border border-border-color space-y-3 relative group/comp">
                                                    <button
                                                        onClick={() => removeUiComponent(caseIdx, compIdx)}
                                                        className="absolute top-2 right-2 text-text-secondary hover:text-red-400 p-1"
                                                        title="Remove Component"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>

                                                    <div className="flex items-center gap-4">
                                                        <div className="space-y-1 flex-1">
                                                            <label className="block text-xs text-text-secondary">Component ID</label>
                                                            <input
                                                                type="number"
                                                                value={comp.id}
                                                                onChange={(e) => updateUiComponentId(caseIdx, compIdx, e.target.value)}
                                                                className="w-full px-2 py-1 bg-bg-app border border-border-color rounded text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                            />
                                                        </div>
                                                    </div>

                                                    {/* Parameters (Key-Value Pairs) */}
                                                    <div className="space-y-2">
                                                        <div className="flex items-center justify-between">
                                                            <label className="text-xs text-text-secondary">Parameters</label>
                                                            <button onClick={() => addUiParameter(caseIdx, compIdx)} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                                                                <Plus size={12} /> Add Parameter
                                                            </button>
                                                        </div>

                                                        {comp.parametersList.map((param, paramIdx) => (
                                                            <div key={paramIdx} className="flex items-center gap-2">
                                                                <input
                                                                    type="text"
                                                                    value={param.key}
                                                                    onChange={(e) => updateUiParameter(caseIdx, compIdx, paramIdx, 'key', e.target.value)}
                                                                    placeholder="Key (e.g. Kp)"
                                                                    className="flex-1 min-w-0 px-2 py-1 bg-bg-app border border-border-color rounded text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                                />
                                                                <span className="text-text-secondary">:</span>
                                                                <input
                                                                    type="text"
                                                                    value={param.value}
                                                                    onChange={(e) => updateUiParameter(caseIdx, compIdx, paramIdx, 'value', e.target.value)}
                                                                    placeholder="Value (e.g. 0.5)"
                                                                    className="flex-1 min-w-0 px-2 py-1 bg-bg-app border border-border-color rounded text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                                />
                                                                <button
                                                                    onClick={() => removeUiParameter(caseIdx, compIdx, paramIdx)}
                                                                    className="text-text-secondary hover:text-red-400 p-1"
                                                                >
                                                                    <X size={14} />
                                                                </button>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                            <div className="flex items-center justify-start">
                                                <button onClick={() => addUiComponent(caseIdx)} className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors">
                                                    <Plus size={14} /> Add Component
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Action Button */}
                    <button
                        onClick={handleCreateCases}
                        disabled={isLoading}
                        className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold rounded-lg shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? <Loader2 size={20} className="animate-spin" /> : 'Create Cases'}
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
