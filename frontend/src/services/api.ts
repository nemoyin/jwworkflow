const BASE_URL = import.meta.env.VITE_API_URL || '/api';

/** 持久化 token 的 localStorage 键（刷新/重启后恢复登录态） */
export const TOKEN_KEY = 'jwworkflow_auth_token';
export const TOKEN_EMAIL_KEY = `${TOKEN_KEY}_email`;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body: any = null,
    public requestId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  // 从 localStorage 恢复，刷新/重启浏览器后仍保持登录态
  private token: string | null = localStorage.getItem(TOKEN_KEY);

  setToken(token: string) { this.token = token; localStorage.setItem(TOKEN_KEY, token); }
  clearToken() { this.token = null; localStorage.removeItem(TOKEN_KEY); }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    // Try to read response body regardless of status
    let responseBody: any = null;
    try {
      responseBody = await res.json();
    } catch {
      try {
        responseBody = await res.text();
      } catch {
        responseBody = null;
      }
    }

    if (!res.ok) {
      // token 过期/无效：清掉本地 token 并整页回登录页（token 已清，刷新后 store 恢复为未登录）
      if (res.status === 401) {
        this.clearToken();
        localStorage.removeItem(TOKEN_EMAIL_KEY);
        if (!location.pathname.startsWith('/login')) {
          location.href = '/login';
        }
      }
      const detail = responseBody?.message || responseBody?.detail || responseBody || `API error: ${res.status}`;
      const requestId = responseBody?.request_id;
      throw new ApiError(
        typeof detail === 'string' ? detail : `请求失败 (${res.status})`,
        res.status,
        responseBody,
        requestId,
      );
    }

    if (res.status === 204) return undefined as T;
    return responseBody as T;
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body?: unknown) { return this.request<T>('POST', path, body); }
  put<T>(path: string, body?: unknown) { return this.request<T>('PUT', path, body); }
  delete(path: string) { return this.request<void>('DELETE', path); }

  /** Upload a file via multipart/form-data */
  async uploadFormData(path: string, formData: FormData): Promise<any> {
    const headers: Record<string, string> = {};
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const res = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new ApiError(`上传失败: ${res.status} ${text.slice(0, 200)}`, res.status, text);
    }
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
