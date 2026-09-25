import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { getMetrics, getTraining, startTraining } from "../services/trainingService";

export function TrainingPage() {
  const { modelId } = useParams();
  const [job, setJob] = useState(null);
  const [metrics, setMetrics] = useState({});
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);

  async function loadTraining() {
    setIsLoading(true);
    setError("");
    try {
      const [trainingResponse, metricsResponse] = await Promise.all([
        getTraining(modelId),
        getMetrics(modelId),
      ]);
      setJob(trainingResponse.job);
      setMetrics(metricsResponse.metrics);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadTraining();
  }, [modelId]);

  async function handleStart() {
    setError("");
    setIsStarting(true);
    try {
      const response = await startTraining(modelId);
      setJob(response.job);
      setMetrics(response.job.metrics || {});
    } catch (requestError) {
      await loadTraining();
      setError(requestError.message);
    } finally {
      setIsStarting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading training status..." />;
  }

  return (
    <section>
      <Link className="text-sm text-slate-400 hover:text-slate-200" to={`/models/${modelId}`}>
        ← Back to model
      </Link>
      <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-cyan-300">Model workflow</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Training</h1>
          <p className="mt-3 text-sm text-slate-400">Train the selected pipeline and review evaluation metrics.</p>
        </div>
        <button
          className="rounded-md bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isStarting}
          onClick={handleStart}
          type="button"
        >
          {isStarting ? "Training..." : job?.status === "COMPLETED" ? "Retrain model" : "Start training"}
        </button>
      </div>

      {error ? <div className="mt-6"><ErrorState message={error} onRetry={loadTraining} /></div> : null}

      {job ? (
        <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Latest job</p>
              <p className="mt-2 text-lg font-semibold text-slate-100">{job.status}</p>
            </div>
            <span className="text-sm text-slate-400">{job.progress}% complete</span>
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full rounded-full bg-cyan-400 transition-all" style={{ width: `${job.progress}%` }} />
          </div>
          {job.error_message ? <p className="mt-4 text-sm text-red-300">{job.error_message}</p> : null}
        </div>
      ) : (
        <div className="mt-8 rounded-xl border border-dashed border-slate-700 px-6 py-12 text-center text-sm text-slate-500">
          No training job has been started for this model.
        </div>
      )}

      {Object.keys(metrics).length ? (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-slate-100">Evaluation metrics</h2>
          <p className="mt-2 text-sm text-slate-400">Metrics use weighted averages for multiclass classification.</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ...(metrics.accuracy !== undefined
                ? [["Accuracy", metrics.accuracy], ["Precision", metrics.precision], ["Recall", metrics.recall], ["F1 score", metrics.f1]]
                : [["MAE", metrics.mae], ["RMSE", metrics.rmse], ["R²", metrics.r2]]),
            ].map(([label, value]) => (
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5" key={label}>
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-100">{Number(value).toFixed(3)}</p>
              </div>
            ))}
          </div>
          {metrics.confusion_matrix ? <div className="mt-6 overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Confusion matrix</p>
            <div className="mt-4 inline-grid gap-1" style={{ gridTemplateColumns: `repeat(${metrics.confusion_matrix?.[0]?.length || 1}, minmax(3rem, 1fr))` }}>
              {metrics.confusion_matrix?.flat().map((value, index) => <span className="rounded bg-slate-800 px-3 py-2 text-center text-sm text-slate-200" key={index}>{value}</span>)}
            </div>
          </div> : null}
        </div>
      ) : null}
    </section>
  );
}
