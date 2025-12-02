// API configuration
// In production, uses relative URLs (same domain)
// In development, uses localhost:8000

const getApiBaseUrl = (): string => {
  // If we're in development (localhost), use localhost:8000
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  // In production, use relative URLs (same domain)
  return '';
};

export const API_BASE_URL = getApiBaseUrl();

export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return API_BASE_URL ? `${API_BASE_URL}/${cleanEndpoint}` : `/${cleanEndpoint}`;
};

export const getWebSocketUrl = (path: string): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname;
  const port = window.location.port;
  
  // If we're in development (localhost), use localhost:8000
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `ws://localhost:8000${path}`;
  }
  // In production, use the same domain with appropriate protocol
  const host = port ? `${hostname}:${port}` : hostname;
  return `${protocol}//${host}${path}`;
};
