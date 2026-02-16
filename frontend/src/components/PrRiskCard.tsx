import React from "react";

interface FileBreakdown {
  file: string;
  risk_score: number;
  risk_level: string;
  direct_dependents: number;
  transitive_dependents: number;
  depth: number;
}

interface AiAnalysis {
  review_focus: string;
  testing_strategy: string;
  merge_readiness: string;
  risk_explanation: string;
}

export interface PrRiskResponse {
  pr_risk_score: number;
  classification: string;
  total_files_affected: number;
  max_impact_depth: number;
  high_risk_modules: string[];
  file_breakdown: FileBreakdown[];
  ai_analysis: AiAnalysis;
}

const getRiskColor = (level: string) => {
  switch (level) {
    case "CRITICAL":
      return "bg-red-700";
    case "HIGH":
      return "bg-orange-500";
    case "MODERATE":
      return "bg-yellow-500";
    case "LOW":
      return "bg-green-500";
    default:
      return "bg-gray-400";
  }
};

const PRRiskCard: React.FC<{ data: PrRiskResponse }> = ({ data }) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border w-full max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">PR Risk Analysis</h2>
        <span
          className={`px-4 py-1 rounded-full text-white text-sm font-semibold ${getRiskColor(
            data.classification
          )}`}
        >
          {data.classification}
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-100 rounded-xl p-4 text-center">
          <p className="text-sm text-gray-500">Risk Score</p>
          <p className="text-xl font-bold">{data.pr_risk_score}</p>
        </div>

        <div className="bg-gray-100 rounded-xl p-4 text-center">
          <p className="text-sm text-gray-500">Files Affected</p>
          <p className="text-xl font-bold">{data.total_files_affected}</p>
        </div>

        <div className="bg-gray-100 rounded-xl p-4 text-center">
          <p className="text-sm text-gray-500">Max Impact Depth</p>
          <p className="text-xl font-bold">{data.max_impact_depth}</p>
        </div>
      </div>

      {/* High Risk Modules */}
      {data.high_risk_modules.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold mb-2 text-red-600">
            High Risk Modules
          </h3>
          <ul className="list-disc list-inside text-sm">
            {data.high_risk_modules.map((module, index) => (
              <li key={index}>{module}</li>
            ))}
          </ul>
        </div>
      )}

      {/* AI Analysis */}
      <div className="bg-gray-50 p-4 rounded-xl border">
        <h3 className="font-semibold mb-3">AI Review Summary</h3>

        <p className="text-sm mb-2">
          <strong>Review Focus:</strong> {data.ai_analysis.review_focus}
        </p>

        <p className="text-sm mb-2">
          <strong>Testing Strategy:</strong>{" "}
          {data.ai_analysis.testing_strategy}
        </p>

        <p className="text-sm mb-2">
          <strong>Merge Readiness:</strong>{" "}
          <span
            className={
            data.ai_analysis.merge_readiness === "LOW"
              ? "text-red-600 font-semibold"
              : data.ai_analysis.merge_readiness === "MEDIUM"
              ? "text-yellow-600 font-semibold"
              : "text-green-600 font-semibold"
          }

          >
            {data.ai_analysis.merge_readiness}
          </span>
        </p>

        <p className="text-sm text-gray-700">
          {data.ai_analysis.risk_explanation}
        </p>
      </div>
    </div>
  );
};

export default PRRiskCard;
