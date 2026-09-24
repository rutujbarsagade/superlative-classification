import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { getAdminDashboard } from "../services/adminService";

export function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  async function loadDashboard() {
    setIsLoading(true);
    setError("");
    try {
      setDashboard(await getAdminDashboard());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (isLoading) {
    return <LoadingState label="Loading administration overview..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadDashboard} />;
  }

  const metrics = [
    ["Total users", dashboard.total_users],
    ["Developers", dashboard.developers],
    ["Pending approvals", dashboard.pending_developers],
    ["Approved developers", dashboard.approved_developers],
    ["Rejected developers", dashboard.rejected_developers],
  ];

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-cyan-300">Administration</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Platform overview</h1>
          <p className="mt-3 text-sm text-slate-400">Real account counts from the user registry.</p>
        </div>
        <Link className="text-sm text-cyan-300 hover:text-cyan-200" to="/admin/approvals">
          Review pending approvals
        </Link>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {metrics.map(([label, value]) => (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5" key={label}>
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
            <p className="mt-3 text-3xl font-semibold text-slate-100">{value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

