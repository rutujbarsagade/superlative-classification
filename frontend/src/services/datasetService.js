import { apiRequest } from "./apiClient";

export function getDataset(modelId) {
  return apiRequest(`/models/${modelId}/dataset/`);
}

export function uploadDataset(modelId, file) {
  const body = new FormData();
  body.append("file", file);
  return apiRequest(`/models/${modelId}/dataset/`, {
    method: "POST",
    body,
  });
}

export function selectTargetColumn(modelId, targetColumn) {
  return apiRequest(`/models/${modelId}/dataset/target/`, {
    method: "POST",
    body: { target_column: targetColumn },
  });
}
