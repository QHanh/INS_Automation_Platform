import { useState } from 'react';
import { open } from '@tauri-apps/plugin-dialog';

export const useFileDialog = () => {
    const [selectedPath, setSelectedPath] = useState<string>('');

    const selectFile = async (filters?: { name: string; extensions: string[] }[]) => {
        try {
            const selected = await open({
                multiple: false,
                directory: false,
                filters,
            });

            if (selected) {
                setSelectedPath(selected);
                return selected;
            }
            return null;
        } catch (error) {
            console.error('Error selecting file:', error);
            return null;
        }
    };

    const selectFolder = async () => {
        try {
            const selected = await open({
                multiple: false,
                directory: true,
            });

            if (selected) {
                setSelectedPath(selected);
                return selected;
            }
            return null;
        } catch (error) {
            console.error('Error selecting folder:', error);
            return null;
        }
    };

    return {
        selectedPath,
        selectFile,
        selectFolder,
    };
};
