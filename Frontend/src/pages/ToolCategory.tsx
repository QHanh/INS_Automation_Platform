import { useParams, useNavigate } from 'react-router-dom';
import BackButton from '../components/BackButton';

const toolsData = {
    pscad: [
        { id: 'build-model', name: 'Build model' },
        { id: 'setup-case', name: 'Setup case' },
        { id: 'auto-tuning', name: 'Auto tuning' },
        { id: 'generate-report', name: 'Generate report' },
    ],
    psse: [
        { id: 'build-model', name: 'Build model' },
        { id: 'check-reactive', name: 'Check reactive' },
        { id: 'tuning-tool', name: 'Tuning P/Q' },
        { id: 'dmview', name: 'DMView' },
        { id: 'setup-case', name: 'Setup case' },
        { id: 'auto-tuning-dynamic', name: 'Auto tuning dynamic' },
        { id: 'generate-report', name: 'Generate report' },
    ],
    etap: [
        { id: 'build-model', name: 'Build model' },
        { id: 'tuning-rp', name: 'Tuning RP' },
        { id: 'export-results-sc', name: 'Export results SC' },
        { id: 'generate-report', name: 'Generate report' },
    ],
};

const categoryNames = {
    pscad: 'PSCAD Tools',
    psse: 'PSS/E Tools',
    etap: 'ETAP Tools',
};

export default function ToolCategory() {
    const { category } = useParams<{ category: string }>();
    const navigate = useNavigate();
    const tools = toolsData[category as keyof typeof toolsData] || [];
    const categoryName = categoryNames[category as keyof typeof categoryNames] || category;

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border-color flex items-center gap-4">
                <BackButton />
                <h1 className="text-lg font-semibold">{categoryName}</h1>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                <div className="grid gap-3">
                    {tools.map((tool) => (
                        <button
                            key={tool.id}
                            onClick={() => navigate(`/${category}/${tool.id}`)}
                            className="w-full bg-bg-surface hover:bg-white/5 border border-border-color 
                rounded-lg p-4 text-left transition-colors"
                        >
                            <h3 className="font-semibold text-text-primary">{tool.name}</h3>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
