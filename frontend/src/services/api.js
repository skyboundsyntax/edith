/**
 * API Service Client for EDITH Data Intelligence Platform.
 * Connects strictly to FastAPI Backend and WebSockets for real-time streaming.
 * Adheres to SDD specifications.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export const api = {
  // --- Workflows (SDD 2.2) ---
  async getWorkflows() {
    const res = await fetch(`${API_BASE}/workflows`);
    if (!res.ok) throw new Error('Failed to fetch workflows');
    return res.json();
  },

  async createWorkflow(prompt, confidenceThreshold = 80.0) {
    const res = await fetch(`${API_BASE}/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, confidence_threshold: confidenceThreshold })
    });
    if (!res.ok) throw new Error('Failed to create workflow');
    return res.json();
  },

  async getWorkflowDetails(id) {
    const res = await fetch(`${API_BASE}/workflows/${id}`);
    if (!res.ok) throw new Error('Failed to fetch workflow details');
    return res.json();
  },

  // --- Datasets & Provenance Lineage (SDD Section 3) ---
  async getDatasets(params = {}) {
    const query = new URLSearchParams();
    if (params.workflow_id) query.append('workflow_id', params.workflow_id);
    if (params.min_confidence) query.append('min_confidence', params.min_confidence);
    if (params.human_review_only) query.append('human_review_only', 'true');
    if (params.search) query.append('search', params.search);

    const res = await fetch(`${API_BASE}/datasets?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch datasets');
    return res.json();
  },

  async getRecordProvenance(recordId) {
    const res = await fetch(`${API_BASE}/datasets/${recordId}/provenance`);
    if (!res.ok) throw new Error('Failed to fetch provenance');
    return res.json();
  },

  async reviewRecord(recordId, action) {
    const res = await fetch(`${API_BASE}/datasets/${recordId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    if (!res.ok) throw new Error('Failed to review record');
    return res.json();
  },

  // --- Export Service (CSV / JSON) ---
  async exportDataset(format = 'json', workflowId = null, minConfidence = null) {
    const res = await fetch(`${API_BASE}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        format,
        workflow_id: workflowId,
        min_confidence: minConfidence
      })
    });
    if (!res.ok) throw new Error('Export failed');
    return res.json();
  },

  // --- WebSocket Live Telemetry Stream (SDD 2.2) ---
  connectWebSocket(workflowId, onMessage, onError) {
    const wsUrl = workflowId ? `${WS_BASE}/workflows/${workflowId}` : `${WS_BASE}/live`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log(`WebSocket connected to ${wsUrl}`);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    return socket;
  }
};
