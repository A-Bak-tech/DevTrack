
const API_BASE = '/api/v1/auth'

export type User = {
  id: string
  email: string
}

export type AuthCredentials = {
  email: string
  password: string
}

type ApiError = {
  detail?: string
}

async function checkResponse(
  response: Response,
): Promise<void> {
  if (response.ok) return

  let message = 'Something went wrong.'

  try {
    const error = (await response.json()) as ApiError

    if (typeof error.detail === 'string') {
      message = error.detail
    }
  } catch {
    // Use the default error message.
  }

  throw new Error(message)
}

export async function registerUser(
  credentials: AuthCredentials,
): Promise<User> {
  const response = await fetch(`${API_BASE}/register`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  })

  await checkResponse(response)

  return (await response.json()) as User
}

export async function loginUser(
  credentials: AuthCredentials,
): Promise<void> {
  const response = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  })

  await checkResponse(response)
}

export async function getCurrentUser(): Promise<User | null> {
  const response = await fetch(`${API_BASE}/me`, {
    credentials: 'include',
  })

  if (response.status === 401) {
    return null
  }

  await checkResponse(response)

  return (await response.json()) as User
}

export async function getCsrfToken(): Promise<string> {
  const response = await fetch(`${API_BASE}/csrf`, {
    credentials: 'include',
  })

  await checkResponse(response)

  const data = (await response.json()) as {
    csrf_token: string
  }

  return data.csrf_token
}

export async function logoutUser(): Promise<void> {
  const csrfToken = await getCsrfToken()

  const response = await fetch(`${API_BASE}/logout`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRF-Token': csrfToken,
    },
  })

  await checkResponse(response)
}
