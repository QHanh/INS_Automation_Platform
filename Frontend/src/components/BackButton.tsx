import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function BackButton() {
    const navigate = useNavigate();

    return (
        <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg bg-bg-surface hover:bg-white/10 border border-border-color
        text-text-secondary hover:text-text-primary transition-colors"
            title="Back"
        >
            <ArrowLeft size={20} />
        </button>
    );
}
