const BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) { this.token = token; }
  clearToken() { this.token = null; }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    if (res.status === 204) return undefined as T;
    return res.json();
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body?: unknown) { return this.request<T>('POST', path, body); }
  put<T>(path: string, body?: unknown) { return this.request<T>('PUT', path, body); }
  delete(path: string) { return this.request<void>('DELETE', path); }

  /** Upload a file via multipart/form-data */
  async uploadDocument(file: File): Promise<KnowledgeDocument> {
    const headers: Record<string, string> = {};
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/knowledge/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  }

  /** List all knowledge documents */
  listDocuments() { return this.get<KnowledgeListResponse>('/knowledge'); }

  /** Delete a knowledge document by ID */
  deleteDocument(id: string) { return this.delete(`/knowledge/${id}`); }
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  content_type: string;
  file_size: number;
  status: string;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeListResponse {
  documents: KnowledgeDocument[];
  total: number;
}

export const api = new ApiClient();
