import { useState } from "react";
import axios from "axios";
import PRRiskCard from "./PrRiskCard";

interface AnalysisItem {
  file: string;
  risk_score: number;
  risk_level: string;
  direct_dependents: number;
  transitive_dependents: number;
  depth: number;
}

interface ExecutiveSummary {
  severity: string;
  why_risky: string;
  testing_recommendation: string;
  developer_action: string;
}

interface ImpactResponse {
  analysis: AnalysisItem[];
  executive_summary: ExecutiveSummary;
}

interface Props {
  folderName: string;
}

export default function PredictChangeRisk({ folderName }: Props) {
  const [fileName, setFileName] = useState("");
  const [impactResult, setImpactResult] = useState<ImpactResponse | null>(null);
  const [prRiskResult, setPrRiskResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const analyzeImpact = async () => {
    if (!folderName || !fileName) return;

    setLoading(true);
    setImpactResult(null);
    setPrRiskResult(null);

    try {
      // 1️⃣ Impact Analysis
      const impactRes = await axios.post(
        "http://127.0.0.1:8000/impact-analysis",
        {
          folder_name: folderName,
          changed_files: [fileName],
        }
      );

      setImpactResult(impactRes.data);

      // 2️⃣ PR Risk Analysis
      const prRiskRes = await axios.post(
        "http://127.0.0.1:8000/pr-risk-analysis",
        {
          folder_name: folderName,
          changed_files: [fileName],
        }
      );

      setPrRiskResult(prRiskRes.data);

    } catch (error) {
      alert("Failed to analyze change risk");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const severityColor = (level: string) => {
    switch (level) {
      case "HIGH":
        return "bg-red-500";
      case "MEDIUM":
        return "bg-yellow-500";
      case "LOW":
        return "bg-green-500";
      default:
        return "bg-gray-400";
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800">
        🚀 Predict Change Risk
      </h2>

      {/* Input Section */}
      <div className="grid md:grid-cols-3 gap-4 items-end">
        <div>
          <label className="text-sm font-medium text-gray-600">
            Folder Name
          </label>
          <input
            value={folderName}
            disabled
            className="w-full mt-1 p-3 rounded-lg border bg-gray-100"
          />
        </div>

        <div>
          <label className="text-sm font-medium text-gray-600">
            Changed File
          </label>
          <input
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
            placeholder="lib/utils.js"
            className="w-full mt-1 p-3 rounded-lg border focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <button
          onClick={analyzeImpact}
          className="h-[46px] bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-all"
        >
          {loading ? "Analyzing..." : "Analyze Impact"}
        </button>
      </div>

      {/* Impact Result Section */}
      {impactResult && (
        <div className="bg-gray-50 border rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800">
              Impact Analysis
            </h3>

            <span
              className={`px-4 py-1 text-white text-sm font-semibold rounded-full ${severityColor(
                impactResult.executive_summary.severity
              )}`}
            >
              {impactResult.executive_summary.severity}
            </span>
          </div>

          <div className="grid md:grid-cols-4 gap-4 text-center">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <p className="text-gray-500 text-sm">Risk Score</p>
              <p className="text-xl font-bold">
                {impactResult.analysis[0].risk_score}
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm">
              <p className="text-gray-500 text-sm">Direct</p>
              <p className="text-xl font-bold">
                {impactResult.analysis[0].direct_dependents}
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm">
              <p className="text-gray-500 text-sm">Transitive</p>
              <p className="text-xl font-bold">
                {impactResult.analysis[0].transitive_dependents}
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm">
              <p className="text-gray-500 text-sm">Depth</p>
              <p className="text-xl font-bold">
                {impactResult.analysis[0].depth}
              </p>
            </div>
          </div>

          <div className="space-y-2 text-gray-700">
            <p>
              <strong>Why Risky:</strong>{" "}
              {impactResult.executive_summary.why_risky}
            </p>
            <p>
              <strong>Testing Recommendation:</strong>{" "}
              {impactResult.executive_summary.testing_recommendation}
            </p>
            <p>
              <strong>Developer Action:</strong>{" "}
              {impactResult.executive_summary.developer_action}
            </p>
          </div>
        </div>
      )}

      {/* PR Risk Card Section */}
      {prRiskResult && (
        <div className="mt-6">
          <PRRiskCard data={prRiskResult} />
        </div>
      )}
    </div>
  );
}
