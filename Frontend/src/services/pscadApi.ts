// API service for PSCAD endpoints
const API_BASE_URL = 'http://localhost:8123/api';

export interface BuildModelRequest {
    file_path: string
}

export interface PSCADComponent {
    id: number;
    parameters: Record<string, any>;
}

export interface PSCADCase {
    new_filename: string;
    components: PSCADComponent[];
}

export interface CreateCasesRequest {
    project_path: string;
    original_filename: string;
    cases: PSCADCase[];
}

export interface ConvertSimulinkRequest {
    simulink_folder: string;
    output_path?: string;
}

export interface ApiResponse<T = unknown> {
    success: boolean;
    data?: T;
    error?: string;
}

export const pscadApi = {
    async buildEquivalentModel(data: BuildModelRequest): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/pscad/build-equivalent-model`, {
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

    async createCases(data: CreateCasesRequest): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/pscad/create-cases`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
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

    async convertSimulink(data: ConvertSimulinkRequest): Promise<ApiResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/pscad/convert-simulink`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
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
