
export interface HealthResponse {
  status: string
  service: string
}

export async function getBackendHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/v1/health', {
    method: 'GET',
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new Error(`Backend returned HTTP ${response.status}`)
  }

  return (await response.json()) as HealthResponse
}
