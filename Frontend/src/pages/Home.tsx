import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import pscadIcon from '../assets/PSCAD-Icon.png';
import psseIcon from '../assets/PSSE-Icon.png';
import etapIcon from '../assets/ETAP-Icon.png';

const GRID_COLS = 4;
const GRID_ROWS = 5;
const STORAGE_KEY = 'tool-grid-positions';

interface ToolItem {
    id: string;
    name: string;
    icon: string;
}

const defaultTools: ToolItem[] = [
    { id: 'pscad', name: 'PSCAD', icon: pscadIcon },
    { id: 'psse', name: 'PSS/E', icon: psseIcon },
    { id: 'etap', name: 'ETAP', icon: etapIcon },
];

const defaultPositions: Record<string, number> = {
    pscad: 0,
    psse: 1,
    etap: 2,
};

export default function Home() {
    const navigate = useNavigate();
    const [positions, setPositions] = useState<Record<string, number>>(() => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            return saved ? JSON.parse(saved) : defaultPositions;
        } catch {
            return defaultPositions;
        }
    });
    const [dragging, setDragging] = useState<{ toolId: string; startSlot: number } | null>(null);
    const [hoverSlot, setHoverSlot] = useState<number | null>(null);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(positions));
    }, [positions]);

    const handleMouseDown = useCallback((e: React.MouseEvent, toolId: string, slot: number) => {
        e.preventDefault();
        setDragging({ toolId, startSlot: slot });
    }, []);

    const handleMouseUp = useCallback(() => {
        if (dragging && hoverSlot !== null && hoverSlot !== dragging.startSlot) {
            const targetSlot = hoverSlot;
            const occupyingTool = Object.entries(positions).find(
                ([, pos]) => pos === targetSlot
            )?.[0];

            setPositions(prev => {
                const newPositions = { ...prev };
                if (occupyingTool && occupyingTool !== dragging.toolId) {
                    newPositions[occupyingTool] = dragging.startSlot;
                }
                newPositions[dragging.toolId] = targetSlot;
                return newPositions;
            });
        }
        setDragging(null);
        setHoverSlot(null);
    }, [dragging, hoverSlot, positions]);

    const handleMouseEnter = useCallback((slotIndex: number) => {
        if (dragging) {
            setHoverSlot(slotIndex);
        }
    }, [dragging]);

    const handleClick = useCallback((toolId: string) => {
        if (!dragging) {
            navigate(`/${toolId}`);
        }
    }, [dragging, navigate]);

    useEffect(() => {
        if (dragging) {
            const handleGlobalMouseUp = () => handleMouseUp();
            window.addEventListener('mouseup', handleGlobalMouseUp);
            return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
        }
    }, [dragging, handleMouseUp]);

    const getToolAtSlot = (slotIndex: number): ToolItem | null => {
        const toolId = Object.entries(positions).find(
            ([, pos]) => pos === slotIndex
        )?.[0];
        return defaultTools.find(t => t.id === toolId) || null;
    };

    const totalSlots = GRID_COLS * GRID_ROWS;

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4">
                <div
                    className="grid gap-2 max-w-md mx-auto"
                    style={{ gridTemplateColumns: `repeat(${GRID_COLS}, 1fr)` }}
                >
                    {Array.from({ length: totalSlots }).map((_, index) => {
                        const tool = getToolAtSlot(index);
                        const isHover = hoverSlot === index && dragging;
                        const isDragging = tool && dragging?.toolId === tool.id;

                        return (
                            <div
                                key={index}
                                onMouseEnter={() => handleMouseEnter(index)}
                                className={`
                  aspect-square rounded-lg border border-dashed transition-all duration-150
                  ${isHover
                                        ? 'border-blue-500 bg-blue-500/20 scale-105'
                                        : 'border-white/5 hover:border-white/10'
                                    }
                  ${tool ? 'border-solid border-white/10' : ''}
                `}
                            >
                                {tool && (
                                    <div
                                        onMouseDown={(e) => handleMouseDown(e, tool.id, index)}
                                        onClick={() => handleClick(tool.id)}
                                        className={`
                      w-full h-full rounded-lg bg-bg-surface border border-white/10 
                      hover:border-blue-500/50 hover:bg-blue-500/5
                      flex flex-col items-center justify-center gap-1.5
                      transition-all duration-150 select-none
                      ${isDragging ? 'opacity-50 scale-90 cursor-grabbing' : 'cursor-pointer'}
                    `}
                                    >
                                        <img
                                            src={tool.icon}
                                            alt={tool.name}
                                            className="w-8 h-8 object-contain rounded-md pointer-events-none select-none"
                                            draggable={false}
                                        />
                                        <span className="text-xs font-medium text-text-primary pointer-events-none select-none">
                                            {tool.name}
                                        </span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Instructions */}
                <p className="text-center text-xs text-text-secondary mt-4">
                    Hold and drag to move tools
                </p>
            </div>
        </div>
    );
}
