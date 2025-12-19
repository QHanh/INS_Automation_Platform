const API_BASE_URL = 'http://localhost:8123/api';

export interface EtapBuildModelRequest {
    cls_file_path: string;
    pcs_file_path: string;
    mpt_type: 'XFORM3W' | 'XFORM2W';
    create_sld_elements: boolean;
    create_poi_to_mpt_elements: boolean;
    connect_elements: boolean;
}

export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
}

const post = async <T>(endpoint: string, data: any): Promise<ApiResponse<T>> => {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: String(error) };
    }
};

export const etapApi = {
    createBessSld: (data: EtapBuildModelRequest) => post('/etap/create-bess-sld', data),
    createPvSld: (data: EtapBuildModelRequest) => post('/etap/create-pv-sld', data),
    createWtSld: (data: EtapBuildModelRequest) => post('/etap/create-wt-sld', data),
};
