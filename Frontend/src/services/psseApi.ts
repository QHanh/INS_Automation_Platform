// API service for PSS/E endpoints
const API_BASE_URL = 'http://localhost:8123/api';

export interface BuildModelRequest {
    file_path: string;
    output_path: string;
}

export interface ApiResponse<T = unknown> {
    success: boolean;
    data?: T;
    error?: string;
}

export interface TuningRequest {
    sav_path: string;
    log_path?: string;
    bus_from: number;
    bus_to: number;
    gen_buses: number[];
    gen_ids: string[];
    reg_bus: number[];
    p_target: number;
    q_target: number;
}

export const psseApi = {
    async buildEquivalentModel(data: BuildModelRequest): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/psse/build-equivalent-model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
            };
        }
    },

    async buildDetailedModel(data: BuildModelRequest): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/psse/build-detailed-model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
            };
        }
    },

    async checkReactive(data: { file_path: string }): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/psse/check-reactive`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
            };
        }
    },

    async tuneModel(mode: 'P' | 'Q' | 'PQ', data: TuningRequest): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/psse/tune/${mode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
            };
        }
    },
};
