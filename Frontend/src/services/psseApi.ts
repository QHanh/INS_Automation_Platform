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

export interface MptItem {
    mpt_type: "2-WINDING" | "3-WINDING";
    mpt_from: number;
    mpt_to: number;
    mpt_bus_3?: number;
}

export interface ShuntItem {
    BUS: number;
    ID: string;
}

export interface ReportPointItem {
    bess_id: string;
    name: string;
    bus_from: number;
    bus_to: number;
}

export interface ReactiveCheckConfig {
    SAV_PATH: string;
    MPT_LIST: MptItem[];
    SHUNT_LIST: ShuntItem[];
    REG_BUS: number[];
    GEN_BUSES: number[];
    GEN_IDS: string[];
    BUS_FROM: number;
    BUS_TO: number;
    P_NET: number;
    LOG_PATH?: string;
    REPORT_POINTS: ReportPointItem[];
}

export interface GeneratorGroup {
    buses: number[];
    ids: string[];
    reg_buses: number[];
}

export interface BasicModelRequest {
    sav_path: string;
    project_type: string;
    bus_from: number;
    bus_to: number;
    p_net: number;
    q_target?: number;
    bess_generators?: GeneratorGroup;
    pv_generators?: GeneratorGroup;
    log_path?: string;
}

export interface BasicModelResponse {
    message: string;
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
        // ... (start of existing object)
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

    async checkReactive(data: ReactiveCheckConfig): Promise<ApiResponse> {
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

    async createBasicModel(data: BasicModelRequest): Promise<ApiResponse<BasicModelResponse>> {
        try {
            const response = await fetch(`${API_BASE_URL}/psse/basic-model`, {
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
