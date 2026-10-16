"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Users,
  Globe,
  Eye,
  Activity,
  Search,
  RefreshCw,
  Download,
  ShieldCheck,
  KeyRound,
  ArrowLeft,
  ExternalLink,
  MapPin,
  Clock,
  Laptop,
} from "lucide-react";

interface VisitorRecord {
  ip: string;
  country?: string;
  city?: string;
  region?: string;
  firstSeen?: string;
  lastSeen?: string;
  visits?: string | number;
  userAgent?: string;
}

interface StatsResponse {
  connected: boolean;
  message?: string;
  totalUniqueVisitors: number;
  totalVisits: number;
  countryUniqueVisitors: Record<string, string | number>;
  countryTotalVisits: Record<string, string | number>;
  visitors: VisitorRecord[];
}

export default function AdminDashboard() {
  const [adminKey, setAdminKey] = useState<string>("");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Initialize key from URL or sessionStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlKey = params.get("key");
      const storedKey = sessionStorage.getItem("braille_admin_key");
      const initialKey = urlKey || storedKey || "";
      if (initialKey) {
        setAdminKey(initialKey);
        fetchStats(initialKey);
      }
    }
  }, []);

  async function fetchStats(keyToUse: string) {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/admin/stats?key=${encodeURIComponent(keyToUse)}`);
      if (res.status === 401) {
        setIsAuthenticated(false);
        setErrorMsg("Incorrect Admin Key. Please check the passcode and try again.");
        setLoading(false);
        return;
      }
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data: StatsResponse = await res.json();
      setStats(data);
      setIsAuthenticated(true);
      sessionStorage.setItem("braille_admin_key", keyToUse);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load visitor statistics.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!adminKey.trim()) return;
    fetchStats(adminKey.trim());
  }

  function handleExportCsv() {
    if (!stats || !stats.visitors || stats.visitors.length === 0) return;

    const headers = ["IP Address", "Country", "City", "Region", "Visits", "First Seen", "Last Seen", "User Agent"];
    const rows = stats.visitors.map((v) => [
      `"${v.ip || ""}"`,
      `"${v.country || "Unknown"}"`,
      `"${v.city || "Unknown"}"`,
      `"${v.region || ""}"`,
      `"${v.visits || 1}"`,
      `"${v.firstSeen || ""}"`,
      `"${v.lastSeen || ""}"`,
      `"${(v.userAgent || "").replace(/"/g, '""')}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `braille_visitors_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Filter visitors by IP, country, or city
  const filteredVisitors = useMemo(() => {
    if (!stats?.visitors) return [];
    if (!searchQuery.trim()) return stats.visitors;
    const q = searchQuery.toLowerCase().trim();
    return stats.visitors.filter(
      (v) =>
        (v.ip && v.ip.toLowerCase().includes(q)) ||
        (v.country && v.country.toLowerCase().includes(q)) ||
        (v.city && v.city.toLowerCase().includes(q))
    );
  }, [stats?.visitors, searchQuery]);

  // Sort country breakdown by unique visitor count
  const sortedCountries = useMemo(() => {
    if (!stats?.countryUniqueVisitors) return [];
    return Object.entries(stats.countryUniqueVisitors)
      .map(([country, count]) => ({
        country,
        count: Number(count) || 0,
        totalVisits: Number(stats.countryTotalVisits?.[country]) || Number(count),
      }))
      .sort((a, b) => b.count - a.count);
  }, [stats?.countryUniqueVisitors, stats?.countryTotalVisits]);

  // Format date helper
  const formatDate = (isoStr?: string) => {
    if (!isoStr) return "—";
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">Admin Dashboard</h1>
              <p className="text-xs text-slate-400">Permanent Unique Visitor Intelligence</p>
            </div>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-indigo-400" />
                Admin Passcode
              </label>
              <input
                type="password"
                placeholder="Enter admin key (default: braille2026)"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                autoFocus
              />
            </div>

            {errorMsg && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400">
                {errorMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-xl text-sm transition-colors shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Verifying...
                </>
              ) : (
                "Access Dashboard"
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 flex justify-between items-center text-xs text-slate-500">
            <Link href="/" className="hover:text-slate-300 transition-colors flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to App
            </Link>
            <span>v5.0 Permanent IP Tracker</span>
          </div>
        </div>
      </div>
    );
  }

  const avgVisits =
    stats && stats.totalUniqueVisitors > 0
      ? (stats.totalVisits / stats.totalUniqueVisitors).toFixed(1)
      : "1.0";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Navbar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3">
              <Link
                href="/"
                className="p-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl text-slate-400 hover:text-white transition-colors"
                title="Back to Braille Recognition"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
                  Visitor Intelligence
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                    Permanent All-Time
                  </span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Tracking unique visitors by IP address & edge geolocation permanently
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => fetchStats(adminKey)}
              disabled={loading}
              className="px-3.5 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              onClick={handleExportCsv}
              disabled={!stats?.visitors?.length}
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-xl flex items-center gap-2 transition-colors disabled:opacity-50 shadow-lg shadow-indigo-600/20"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Redis Connection Warning (if env vars are not set yet) */}
        {stats && !stats.connected && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
                <Activity className="w-4 h-4" />
                Upstash Redis Not Configured in Vercel
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                To start permanently tracking all visitors across container restarts, set{" "}
                <code className="text-amber-300 bg-amber-950/50 px-1.5 py-0.5 rounded border border-amber-500/20">
                  UPSTASH_REDIS_REST_URL
                </code>{" "}
                and{" "}
                <code className="text-amber-300 bg-amber-950/50 px-1.5 py-0.5 rounded border border-amber-500/20">
                  UPSTASH_REDIS_REST_TOKEN
                </code>{" "}
                in your Vercel Project Settings → Environment Variables.
              </p>
            </div>
            <a
              href="https://console.upstash.com"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs rounded-xl flex items-center gap-1.5 whitespace-nowrap transition-colors"
            >
              Get Free Upstash Keys <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        )}

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800/80 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                All-Time Unique Users
              </span>
              <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">
              {stats?.totalUniqueVisitors.toLocaleString() || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Unique IP addresses permanently recorded</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800/80 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Total Page Visits
              </span>
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
                <Eye className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">
              {stats?.totalVisits.toLocaleString() || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Total page loads & session starts</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800/80 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Countries Reached
              </span>
              <div className="p-2 bg-sky-500/10 text-sky-400 rounded-xl">
                <Globe className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">
              {sortedCountries.length}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Distinct countries worldwide</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800/80 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Avg. Visits / User
              </span>
              <div className="p-2 bg-amber-500/10 text-amber-400 rounded-xl">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">{avgVisits}</div>
            <p className="text-[11px] text-slate-400 mt-1">Average frequency per unique visitor</p>
          </div>
        </div>

        {/* Geolocation Top Countries Breakdown */}
        {sortedCountries.length > 0 && (
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Globe className="w-4 h-4 text-sky-400" />
              Top Visiting Countries
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {sortedCountries.slice(0, 12).map((item) => {
                const pct =
                  stats?.totalUniqueVisitors && stats.totalUniqueVisitors > 0
                    ? Math.round((item.count / stats.totalUniqueVisitors) * 100)
                    : 100;
                return (
                  <div
                    key={item.country}
                    className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-xl flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200 tracking-wide">
                        {item.country}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">{pct}%</span>
                    </div>
                    <div className="mt-2 flex items-baseline justify-between text-xs">
                      <span className="text-slate-400 text-[11px]">{item.count} users</span>
                      <span className="text-slate-500 text-[10px]">{item.totalVisits} views</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Detailed Visitors Table */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden">
          <div className="p-4 md:p-5 border-b border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-400" />
                Permanent IP Visitor Records
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Showing {filteredVisitors.length} of {stats?.visitors?.length || 0} recorded visitors
              </p>
            </div>

            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by IP, Country, or City..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4 font-semibold">IP Address</th>
                  <th className="py-3 px-4 font-semibold">Location</th>
                  <th className="py-3 px-4 font-semibold">Visits</th>
                  <th className="py-3 px-4 font-semibold">First Seen</th>
                  <th className="py-3 px-4 font-semibold">Last Seen</th>
                  <th className="py-3 px-4 font-semibold">User Agent / Device</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-300">
                {filteredVisitors.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                      {loading
                        ? "Loading visitor data..."
                        : searchQuery
                        ? "No visitors matched your search query."
                        : "No visitors recorded yet. Visit the homepage to log your first record!"}
                    </td>
                  </tr>
                ) : (
                  filteredVisitors.map((v, i) => (
                    <tr key={v.ip || i} className="hover:bg-slate-800/20 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-slate-200">
                        <span className="px-2 py-1 rounded-md bg-slate-950 border border-slate-800">
                          {v.ip}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5 font-medium text-slate-200">
                          <MapPin className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                          <span>
                            {v.country || "Unknown"}
                            {v.city && v.city !== "Unknown" ? `, ${v.city}` : ""}
                          </span>
                        </div>
                        {v.region && (
                          <div className="text-[10px] text-slate-500 ml-5 font-mono">
                            Region: {v.region}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {v.visits || 1} {Number(v.visits) === 1 ? "visit" : "visits"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {formatDate(v.firstSeen)}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-medium">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-indigo-400" />
                          {formatDate(v.lastSeen)}
                        </div>
                      </td>
                      <td className="py-3 px-4 max-w-xs truncate text-[11px] text-slate-500" title={v.userAgent}>
                        <div className="flex items-center gap-1.5">
                          <Laptop className="w-3.5 h-3.5 shrink-0 text-slate-600" />
                          <span className="truncate">{v.userAgent || "Unknown Device"}</span>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
