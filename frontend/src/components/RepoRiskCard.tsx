import { useEffect, useState } from "react";

interface RepoRiskData {
  overall_score: number;
  classification: string;
  architecture_score: number;
  dependency_risk: number;
  bus_factor_risk: number;
  volatility_risk: number;
  executive_analysis: {
    executive_summary: {
      overview: string;
    };
    immediate_engineering_action: {
      recommendation: string;
    };
  };
}

interface Props {
  folderName: string;
}

export default function RepoRiskCard({ folderName }: Props) {
  const [data, setData] = useState<RepoRiskData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!folderName) return;

    const fetchRepoRisk = async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/repo-risk-score?folder_name=${folderName}`
        );
        const json = await res.json();
        setData(json);
      } catch (error) {
        console.error("Failed to fetch repo risk:", error);
      }
      setLoading(false);
    };

    fetchRepoRisk();
  }, [folderName]);

  if (!folderName) {
  return (
    <div className="bg-red-500 text-white p-4 rounded-xl">
      Enter a folder name to analyze repository risk.
    </div>
  );
}

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case "HEALTHY":
        return "bg-green-500";
      case "STABLE":
        return "bg-blue-500";
      case "MODERATE RISK":
        return "bg-yellow-500";
      case "HIGH RISK":
        return "bg-red-500";
      case "CRITICAL":
        return "bg-purple-600";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="w-full bg-gray-900 text-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-800">
      <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
        📊 Repository Risk Overview
      </h2>

      {loading && (
        <div className="text-gray-400 animate-pulse">
          Analyzing repository structure...
        </div>
      )}

      {data && (
        <>
          {/* Score Section */}
          <div className="flex items-center gap-6 mb-6">
            <div className="text-5xl font-bold">
              {data.overall_score}
            </div>

            <span
              className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusColor(
                data.classification
              )}`}
            >
              {data.classification}
            </span>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-800 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-400">Architecture</div>
              <div className="text-xl font-semibold">
                {data.architecture_score}
              </div>
            </div>

            <div className="bg-gray-800 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-400">Dependency Risk</div>
              <div className="text-xl font-semibold">
                {data.dependency_risk}
              </div>
            </div>

            <div className="bg-gray-800 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-400">Bus Factor</div>
              <div className="text-xl font-semibold">
                {data.bus_factor_risk}
              </div>
            </div>

            <div className="bg-gray-800 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-400">Volatility</div>
              <div className="text-xl font-semibold">
                {data.volatility_risk}
              </div>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm uppercase tracking-wide text-blue-400 mb-1">
                Executive Summary
              </h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                {data.executive_analysis?.executive_summary?.overview}
              </p>
            </div>

            <div>
              <h3 className="text-sm uppercase tracking-wide text-red-400 mb-1">
                Immediate Engineering Action
              </h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                {
                  data.executive_analysis?.immediate_engineering_action
                    ?.recommendation
                }
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
