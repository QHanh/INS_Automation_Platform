import { useParams } from 'react-router-dom';
import BackButton from './BackButton';

const categoryNames = {
    pscad: 'PSCAD Tools',
    psse: 'PSS/E Tools',
    etap: 'ETAP Tools',
};

export default function ToolPlaceholder() {
    const { category, toolId } = useParams();

    // Helper to format ID back to Title Case (e.g., "build-model" -> "Build Model")
    const toolName = toolId
        ?.split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

    const categoryName = categoryNames[category as keyof typeof categoryNames] || category;
    const breadcrumb = `${categoryName} / ${toolName}`;

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border-color flex items-center gap-4">
                <BackButton />
                <h2 className="text-lg font-semibold">{breadcrumb}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6 flex items-center justify-center">
                <div className="max-w-md w-full bg-bg-surface/50 border border-border-color rounded-2xl p-8 flex flex-col items-center justify-center text-center text-text-secondary">
                    <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4">
                        <svg
                            className="w-8 h-8 opacity-50"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-text-primary mb-2">
                        Work in Progress
                    </h3>
                    <p className="max-w-md">
                        The <strong>{toolName}</strong> interface is currently being built.
                        Check back soon for updates.
                    </p>
                </div>
            </div>
        </div>
    );
}
