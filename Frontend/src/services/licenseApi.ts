

const API_BASE_URL = 'http://localhost:8123/api';

export interface LicenseVerifyResponse {
    success: boolean;
    payload?: any;
    error?: string;
}

export const licenseApi = {
    async verifyLicense(filePath: string): Promise<LicenseVerifyResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/license/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ file_path: filePath }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Verification failed');
            }

            const result = await response.json();
            return { success: true, payload: result.payload };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
            };
        }
    }
};
