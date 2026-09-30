/**
 * API Service Client for EDITH Data Intelligence Platform.
 * Hardened for:
 * - Network timeouts (via AbortController)
 * - Granular HTTP error status categorization (400, 401, 403, 404, 429, 500)
 * - Offline detection & actionable error messages
 * - Safe JSON deserialization & defensive fallbacks
 * - Resilient WebSocket streaming with graceful error boundaries
 */

const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
const defaultWsProto = isHttps ? 'wss:' : 'ws:';
const defaultHost = typeof window !== 'undefined' ? window.location.host : 'localhost:5173';

const API_BASE = import.meta.env.VITE_API_URL || '/api';
const WS_BASE = import.meta.env.VITE_WS_URL || `${defaultWsProto}//${defaultHost}/ws`;

/**
 * Resilient fetch with configurable timeout, offline detection, and status parsing.
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorDetail = '';
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
      } catch {
        try {
          errorDetail = await response.text();
        } catch {
          errorDetail = response.statusText;
        }
      }

      let message = `API [${response.status}]: `;
      if (response.status === 400) {
        message += errorDetail || 'Invalid query format or request payload.';
      } else if (response.status === 401 || response.status === 403) {
        message += errorDetail || 'Access denied or unauthorized source credential.';
      } else if (response.status === 404) {
        message += errorDetail || 'The requested workflow or record was not found.';
      } else if (response.status === 429) {
        message += errorDetail || 'Connector rate limit reached. Backing off before next request.';
      } else if (response.status >= 500) {
        message += errorDetail || 'EDITH backend service encountered an internal error. Verify daemon status.';
      } else {
        message += errorDetail || `Unexpected response status ${response.status}.`;
      }

      const err = new Error(message);
      err.status = response.status;
      err.detail = errorDetail;
      throw err;
    }

    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      const timeoutErr = new Error(`Request timed out after ${timeoutMs / 1000}s. The EDITH backend may be busy or unreachable.`);
      timeoutErr.isTimeout = true;
      throw timeoutErr;
    }
    if (typeof window !== 'undefined' && !window.navigator.onLine) {
      const offlineErr = new Error('Network connection lost. Please check your internet connectivity.');
      offlineErr.isOffline = true;
      throw offlineErr;
    }
    throw err;
  }
}

export const api = {
  // --- Workflows (SDD 2.2) ---
  async getWorkflows() {
    const res = await fetchWithTimeout(`${API_BASE}/workflows`, {}, 12000);
    return res.json();
  },

  // --- Requirements Planning & AI Query Planning ---
  async planRequirements(prompt) {
    const res = await fetchWithTimeout(`${API_BASE}/workflows/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: String(prompt || '').slice(0, 1000) })
    }, 20000);
    return res.json();
  },

  async createWorkflow(prompt, confidenceThreshold = 75.0, querySpec = null) {
    const safeThreshold = Math.min(99, Math.max(1, Number(confidenceThreshold) || 75.0));
    const res = await fetchWithTimeout(`${API_BASE}/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: String(prompt || '').trim().slice(0, 1000),
        confidence_threshold: safeThreshold,
        query_spec: querySpec
      })
    }, 30000);
    return res.json();
  },

  async getWorkflowDetails(id) {
    if (!id) throw new Error('Workflow ID is required');
    const safeId = encodeURIComponent(String(id));
    const res = await fetchWithTimeout(`${API_BASE}/workflows/${safeId}`, {}, 12000);
    return res.json();
  },

  // --- Source Policy Registry & Health Matrix ---
  async getSourcesHealth(force = false) {
    const url = force ? `${API_BASE}/sources/health?force=true` : `${API_BASE}/sources/health`;
    const res = await fetchWithTimeout(url, {}, 15000);
    return res.json();
  },

  // --- Datasets & Provenance Lineage (SDD Section 3) ---
  async getDatasets(params = {}) {
    const query = new URLSearchParams();
    if (params.workflow_id) query.append('workflow_id', String(params.workflow_id));
    if (params.min_confidence) query.append('min_confidence', String(params.min_confidence));
    if (params.human_review_only) query.append('human_review_only', 'true');
    if (params.search) query.append('search', String(params.search).slice(0, 100));

    const res = await fetchWithTimeout(`${API_BASE}/datasets?${query.toString()}`, {}, 15000);
    return res.json();
  },

  async getRecordProvenance(recordId) {
    if (!recordId) throw new Error('Record ID is required for provenance audit');
    const safeId = encodeURIComponent(String(recordId));
    const res = await fetchWithTimeout(`${API_BASE}/datasets/${safeId}/provenance`, {}, 12000);
    return res.json();
  },

  async reviewRecord(recordId, action) {
    if (!recordId) throw new Error('Record ID is required');
    const safeId = encodeURIComponent(String(recordId));
    const res = await fetchWithTimeout(`${API_BASE}/datasets/${safeId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: String(action || 'approve') })
    }, 10000);
    return res.json();
  },

  // --- Export Service (CSV / JSON) ---
  async exportDataset(format = 'csv', workflowId = null, minConfidence = null) {
    const res = await fetchWithTimeout(`${API_BASE}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        format: format === 'json' ? 'json' : 'csv',
        workflow_id: workflowId,
        min_confidence: minConfidence
      })
    }, 25000);
    return res.json();
  },

  // --- WebSocket Live Telemetry Stream (SDD 2.2) ---
  connectWebSocket(workflowId, onMessage, onError) {
    const wsUrl = workflowId ? `${WS_BASE}/workflows/${encodeURIComponent(workflowId)}` : `${WS_BASE}/live`;
    let socket = null;
    let isClosedExplicitly = false;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        // Connected to pipeline
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (err) {
          console.warn('Malformed telemetry frame received:', err);
        }
      };

      socket.onerror = (error) => {
        if (!isClosedExplicitly && onError) {
          onError(error);
        }
      };

      socket.onclose = () => {
        // Graceful stream close
      };
    } catch (e) {
      console.warn('WebSocket initialization failed:', e);
      if (onError) onError(e);
    }

    return {
      close() {
        isClosedExplicitly = true;
        if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
          socket.close();
        }
      },
      get readyState() {
        return socket ? socket.readyState : WebSocket.CLOSED;
      }
    };
  }
};
