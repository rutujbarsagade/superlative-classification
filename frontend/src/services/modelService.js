import { apiRequest } from "./apiClient";

export function listModels() {
  return apiRequest("/models/");
}

export function createModel(model) {
  return apiRequest("/models/", {
    method: "POST",
    body: model,
  });
}

export function getModel(modelId) {
  return apiRequest(`/models/${modelId}/`);
}

export function deleteModel(modelId) {
  return apiRequest(`/models/${modelId}/`, { method: "DELETE" });
}
