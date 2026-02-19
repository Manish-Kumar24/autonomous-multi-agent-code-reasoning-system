import { useState } from "react";
import axios from "axios";
import PredictChangeRisk from "./components/PredictChangeRisk";
import RepoRiskCard from "./components/RepoRiskCard";

const App = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [folderName, setFolderName] = useState("");
  const [output, setOutput] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [files, setFiles] = useState<any[]>([]);
  const [isScanning, setIsScanning] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setOutput("Cloning repository...");

    try {
      const response = await axios.post("http://127.0.0.1:8000/clone-repo", {
        repo_url: repoUrl,
        folder_name: folderName
      });
      setOutput(response.data.message || "Repository cloned successfully!");
    } catch (error) {
      setOutput(error instanceof Error ? error.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const handleScan = async () => {
    if (!folderName) {
      setOutput("Please enter folder name first.");
      return;
    }

    setIsScanning(true);
    setOutput("Scanning repository...");

    try {
      const response = await axios.get(
        `http://127.0.0.1:8000/scan-repo?folder_name=${folderName}`
      );

      setFiles(response.data.files || []);
      setOutput(`Found ${response.data.total_files} files.`);
    } catch (error) {
      setOutput("Failed to scan repository.");
    } finally {
      setIsScanning(false);
    }
  };

  const handleAnalyze = async () => {
    setIsLoading(true);
    setOutput("Analyzing repository with AI...");

    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/summarize-repo?folder_name=${folderName}`
      );

      setOutput(res.data);
    } catch (error) {
      setOutput("Failed to analyze repository.");
    } finally {
      setIsLoading(false);
    }
  };

  const explainFile = async (path: string) => {
  setOutput("Analyzing file like a staff engineer...");

  try {
    const res = await axios.get(
      `http://127.0.0.1:8000/explain-file?path=${encodeURIComponent(path)}`
    );

    setOutput(res.data.explanation);

  } catch {
    setOutput("Failed to analyze file.");
  }
};

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-blue-500 to-indigo-600 animate-gradient-xy p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <header className="text-center">
          <h1 className="text-4xl font-extrabold text-white drop-shadow-lg">
            Autonomous Multi-Agent Code Reasoning
          </h1>
          <p className="text-blue-100 mt-2">
            Enter a repository and folder name to clone and analyze
          </p>
        </header>

        {/* Clone Form */}
        <div className="bg-white/90 backdrop-blur-md shadow-xl rounded-xl p-8 transition-all hover:shadow-2xl">
          <h2 className="text-2xl font-semibold mb-6 text-gray-800">Clone Repository</h2>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="flex flex-col">
              <label htmlFor="repoUrl" className="text-gray-700 font-medium mb-2">
                GitHub Repository URL
              </label>
              <input
                type="text"
                id="repoUrl"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/user/repo.git"
                className="p-3 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-500"
                required
              />
            </div>
            <div className="flex flex-col">
              <label htmlFor="folderName" className="text-gray-700 font-medium mb-2">
                Local Folder Name
              </label>
              <input
                type="text"
                id="folderName"
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                placeholder="MyRepoFolder"
                className="p-3 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-semibold rounded-lg shadow-md flex justify-center items-center gap-2 transition-all disabled:opacity-50"
            >
              {isLoading && (
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                </svg>
              )}
              {isLoading ? "Cloning..." : "Clone Repo"}
            </button>
            <button
              type="button"
              onClick={handleScan}
              disabled={isScanning}
              className="w-full mt-3 py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold rounded-lg shadow-md flex justify-center items-center gap-2 transition-all disabled:opacity-50"
            >
              {isScanning ? "Scanning..." : "Scan Repo"}
            </button>
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold rounded-lg shadow-md mt-4 disabled:opacity-50"
            >
              {isLoading ? "Analyzing..." : "Analyze Repository"}
            </button>


          </form>
        </div>

        {/* Repository Risk Panel */}
        <div className="bg-white/90 backdrop-blur-md shadow-xl rounded-xl p-8 transition-all hover:shadow-2xl">
          <RepoRiskCard folderName={folderName} />
        </div>

        {/* Predict Change Risk Panel */}
        <div className="bg-white/90 backdrop-blur-md shadow-xl rounded-xl p-8 transition-all hover:shadow-2xl">
          <PredictChangeRisk folderName={folderName} />
        </div>

        {/* Output Panel */}
        <div className="bg-gray-100 rounded-md p-4 text-gray-800 min-h-[150px] max-h-[500px] overflow-y-auto">

          {!output && "Output will appear here..."}

          {/* STRING OUTPUT (clone / scan messages) */}
          {typeof output === "string" && (
            <p className="font-mono">{output}</p>
          )}

          {/* AI ANALYSIS */}
          {output?.analysis && (
            <>
              <h3 className="text-xl font-bold mb-2">Architecture Analysis</h3>

              <pre className="bg-black text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                {JSON.stringify(output.analysis, null, 2)}
              </pre>

              <h3 className="text-xl font-bold mt-4 mb-2">
                Executive Explanation
              </h3>

              <p className="leading-relaxed">
                {output.explanation}
              </p>
            </>
          )}

          {/* FILE LIST */}
          {files.length > 0 && (
            <ul className="space-y-1 text-sm font-mono mt-4">
              {files.map((file, index) => (
                <li
                  key={index}
                  className="border-b border-gray-300 pb-1 cursor-pointer hover:text-blue-600"
                  onClick={() => explainFile(file.path)}
                >
                  📄 {file.path}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
export default App;