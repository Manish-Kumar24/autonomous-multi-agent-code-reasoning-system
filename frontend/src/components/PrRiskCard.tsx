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

interface ReviewerSuggestion {
  primary_reviewer: string;
  secondary_reviewer: string;
  approvals_required: number;
  architecture_review: boolean;
  security_review: boolean;
  reason: string;
}

interface TestingRecommendation {
  unit_testing: string;
  integration_testing: string;
  regression_testing: string;
  performance_testing: string;
  security_testing: string;
  test_coverage_target: string;
}

interface Confidence {
  confidence_score: number;
  confidence_level: string;
}

interface MergeControl {
  merge_decision: "BLOCK" | "MANUAL_REVIEW" | "ALLOW_WITH_REVIEW" | "AUTO_APPROVE";
  decision_reason: string;
}

export interface PrRiskResponse {
  pr_risk_score: number;
  classification: string;
  total_files_affected: number;
  max_impact_depth: number;
  high_risk_modules: string[];
  file_breakdown: FileBreakdown[];
  reviewer_suggestion: ReviewerSuggestion;
  testing_recommendation: TestingRecommendation;
  ai_analysis: AiAnalysis;

  confidence: Confidence;
  merge_control: MergeControl;
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

const getDecisionColor = (decision: string) => {
  switch (decision) {
    case "BLOCK":
      return "bg-red-700";
    case "MANUAL_REVIEW":
      return "bg-yellow-600";
    case "ALLOW_WITH_REVIEW":
      return "bg-blue-600";
    case "AUTO_APPROVE":
      return "bg-green-600";
    default:
      return "bg-gray-500";
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

      {/* Merge Decision */}
      {data.merge_control && (
        <div
          className={`mb-6 p-5 rounded-xl text-white font-semibold shadow-md ${getDecisionColor(
            data.merge_control.merge_decision
          )}`}
        >
          <div className="flex justify-between items-center">
            <h3 className="text-lg">Merge Decision</h3>
            <span className="px-3 py-1 bg-white text-black rounded-full text-sm font-bold">
              {data.merge_control.merge_decision}
            </span>
          </div>

          <p className="text-sm mt-3 opacity-90">
            {data.merge_control.decision_reason}
          </p>
        </div>
      )};

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

      {/* Confidence Metric */}
      {data.confidence && (
        <div className="mb-6 bg-purple-50 border border-purple-200 p-4 rounded-xl">
          <h3 className="font-semibold mb-3 text-purple-700">
            📊 Confidence Metric
          </h3>

          <div className="text-sm space-y-2">
            <p>
              <strong>Score:</strong> {data.confidence.confidence_score}
            </p>

            <p>
              <strong>Level:</strong>{" "}
              <span className="font-semibold text-purple-700">
                {data.confidence.confidence_level}
              </span>
            </p>
          </div>
        </div>
      )};

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
      {/* Suggested Reviewers */}
      {data.reviewer_suggestion && (
        <div className="mb-6 bg-blue-50 border border-blue-200 p-4 rounded-xl">
          <h3 className="font-semibold mb-3 text-blue-700">
            👤 Suggested Reviewers
          </h3>

          <div className="text-sm space-y-2">
            <p><strong>Primary:</strong> {data.reviewer_suggestion.primary_reviewer}</p>
            <p><strong>Secondary:</strong> {data.reviewer_suggestion.secondary_reviewer}</p>
            <p><strong>Approvals Required:</strong> {data.reviewer_suggestion.approvals_required}</p>

            <p>
              <strong>Architecture Review:</strong>{" "}
              {data.reviewer_suggestion.architecture_review ? "Required" : "Not Required"}
            </p>

            <p>
              <strong>Security Review:</strong>{" "}
              {data.reviewer_suggestion.security_review ? "Required" : "Not Required"}
            </p>

            <p className="text-gray-600 mt-2">
              {data.reviewer_suggestion.reason}
            </p>
          </div>
        </div>
      )}
      {/* Testing Scope Recommendation */}
      {data.testing_recommendation && (
        <div className="mb-6 bg-green-50 border border-green-200 p-4 rounded-xl">
          <h3 className="font-semibold mb-3 text-green-700">
            🧪 Testing Scope Recommendation
          </h3>

          <div className="text-sm space-y-2">
            <p><strong>Unit Testing:</strong> {data.testing_recommendation.unit_testing}</p>
            <p><strong>Integration Testing:</strong> {data.testing_recommendation.integration_testing}</p>
            <p><strong>Regression Testing:</strong> {data.testing_recommendation.regression_testing}</p>
            <p><strong>Performance Testing:</strong> {data.testing_recommendation.performance_testing}</p>
            <p><strong>Security Testing:</strong> {data.testing_recommendation.security_testing}</p>
            <p><strong>Coverage Target:</strong> {data.testing_recommendation.test_coverage_target}</p>
          </div>
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