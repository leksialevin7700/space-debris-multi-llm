"use client";
import React, { useState, useEffect, useRef } from "react";
import {
  Satellite,
  Upload,
  Map,
  FileText,
  Zap,
  AlertTriangle,
  Clock,
  Activity,
  RefreshCw,
  Play,
  Download,
  Send,
  Database,
  Cpu,
  Brain,
} from "lucide-react";

const OrbitalGuardian = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stats, setStats] = useState({
    totalSatellites: 0,
    closeApproaches: 0,
    highRiskEvents: 0,
    lastAnalysis: null,
  });
  const [riskPairs, setRiskPairs] = useState([]);
  const [logs, setLogs] = useState([]);
  const [satellites, setSatellites] = useState([]);
  const [selectedPair, setSelectedPair] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const canvasRef = useRef(null);
  const [orbitData, setOrbitData] = useState(null);

  // API Base URL - change this to your backend
  const API_BASE = "http://localhost:8000";

  // Fetch dashboard stats
  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  // Fetch risk pairs
  const fetchRiskPairs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/orbit-graph`);
      const data = await res.json();

      // riskPairs should show HIGH-RISK EDGES
      setRiskPairs(data.edges || []);
    } catch (error) {
      console.error("Failed to fetch risks:", error);
    }
  };

  // Fetch orbit graph data
  const fetchOrbitData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/orbit-graph`);
      const data = await res.json();
      setOrbitData(data);
    } catch (error) {
      console.error("Failed to fetch orbit data:", error);
    }
  };

  // Handle TLE file upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    setUploadProgress(0);
    setLogs([]);

    const formData = new FormData();
    formData.append("tle_file", file);

    try {
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData,
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter((l) => l.trim());

        lines.forEach((line) => {
          if (line.startsWith("data: ")) {
            const logEntry = line.slice(6);
            setLogs((prev) => [...prev, logEntry]);
          }
        });

        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }

      setUploadProgress(100);
      await fetchStats();
      await fetchOrbitData();

      const satRes = await fetch(`${API_BASE}/api/satellites`);
      const satData = await satRes.json();
      setSatellites(satData.satellites || []);
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Request maneuver simulation
  const simulateManeuver = async (sat1, sat2, distance) => {
    try {
      const res = await fetch(`${API_BASE}/api/simulate-maneuver`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sat1, sat2, distance }),
      });
      const data = await res.json();
      return data;
    } catch (error) {
      console.error("Simulation failed:", error);
    }
  };

  // Download report
  const downloadReport = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/report/pdf`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `collision_report_${Date.now()}.pdf`;
      a.click();
    } catch (error) {
      console.error("Report download failed:", error);
    }
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    setLogs([]); // Clear previous logs

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("Stream complete");
          break;
        }

        // Decode the chunk
        buffer += decoder.decode(value, { stream: true });

        // Split by newlines to get individual SSE messages
        const lines = buffer.split("\n");

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const jsonStr = line.slice(6); // Remove "data: " prefix
              const data = JSON.parse(jsonStr);

              // Handle different message types
              if (data.log) {
                setLogs((prev) => [...prev, data.log]);
                console.log(`[${data.stage}] ${data.log}`);
              }

              if (data.error) {
                console.error("Error:", data.error);
                setLogs((prev) => [...prev, `❌ Error: ${data.error}`]);
              }

              if (data.summary) {
                console.log("Pipeline summary:", data.summary);
                setLogs((prev) => [
                  ...prev,
                  `📊 Summary: ${data.summary.num_nodes} satellites, ${data.summary.num_edges} close approaches, ${data.summary.high_risk} high-risk events`,
                ]);
              }
            } catch (e) {
              console.error("Failed to parse JSON:", e, "Line:", line);
            }
          }
        }
      }

      // Refresh all data after pipeline completes
      await fetchStats();
      await fetchRiskPairs();
      await fetchOrbitData();

      setLogs((prev) => [...prev, "✅ All data refreshed!"]);
    } catch (error) {
      console.error("Analysis failed:", error);
      setLogs((prev) => [...prev, `❌ Analysis failed: ${error.message}`]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchRiskPairs();
    fetchOrbitData();
  }, []);

  // Canvas animation for orbit visualization
  useEffect(() => {
    if (!canvasRef.current || !orbitData) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    let animationId;
    let rotation = 0;

    const animate = () => {
      ctx.fillStyle = "rgba(2, 6, 23, 0.1)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Draw Earth
      ctx.beginPath();
      ctx.arc(centerX, centerY, 50, 0, Math.PI * 2);
      ctx.fillStyle = "#1e3a8a";
      ctx.fill();
      ctx.strokeStyle = "#3b82f6";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw satellites as nodes
      if (orbitData.nodes) {
        orbitData.nodes.forEach((node, i) => {
          const angle = (i / orbitData.nodes.length) * Math.PI * 2 + rotation;
          const radius = 100 + (i % 3) * 60;
          const x = centerX + Math.cos(angle) * radius;
          const y = centerY + Math.sin(angle) * radius;

          ctx.beginPath();
          ctx.arc(x, y, 4, 0, Math.PI * 2);
          ctx.fillStyle = "#06b6d4";
          ctx.fill();

          // Glow effect
          ctx.shadowBlur = 10;
          ctx.shadowColor = "#06b6d4";
          ctx.fill();
          ctx.shadowBlur = 0;
        });
      }

      // Draw edges (close approaches)
      if (orbitData.edges) {
        orbitData.edges.forEach((edge, i) => {
          const srcIdx = orbitData.nodes.findIndex((n) => n === edge.source);
          const dstIdx = orbitData.nodes.findIndex((n) => n === edge.target);

          if (srcIdx !== -1 && dstIdx !== -1) {
            const angle1 =
              (srcIdx / orbitData.nodes.length) * Math.PI * 2 + rotation;
            const angle2 =
              (dstIdx / orbitData.nodes.length) * Math.PI * 2 + rotation;
            const radius1 = 100 + (srcIdx % 3) * 60;
            const radius2 = 100 + (dstIdx % 3) * 60;

            const x1 = centerX + Math.cos(angle1) * radius1;
            const y1 = centerY + Math.sin(angle1) * radius1;
            const x2 = centerX + Math.cos(angle2) * radius2;
            const y2 = centerY + Math.sin(angle2) * radius2;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);

            const severity =
              edge.risk_score > 0.7
                ? "high"
                : edge.risk_score > 0.4
                ? "medium"
                : "low";
            ctx.strokeStyle =
              severity === "high"
                ? "#ef4444"
                : severity === "medium"
                ? "#f59e0b"
                : "#3b82f6";
            ctx.lineWidth = severity === "high" ? 2 : 1;
            ctx.stroke();
          }
        });
      }

      rotation += 0.002;
      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationId);
  }, [orbitData]);

  const DashboardView = () => (
    <div className="space-y-6 animate-fadeIn">
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 rounded-2xl border border-cyan-500/20 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-2 px-3 py-1 bg-cyan-500/10 rounded-full border border-cyan-500/30">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
              <span className="text-cyan-400 text-xs font-medium">
                LIVE SYSTEM
              </span>
            </div>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent mb-3">
            Multi-LLM Space Debris Intelligence
          </h1>
          <p className="text-gray-400 text-lg">
            Predict, negotiate, and avoid collisions before they happen.
            AI-powered orbital analysis with real-time risk assessment.
          </p>
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={runAnalysis}
          disabled={isAnalyzing}
          className="group relative flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-8 py-4 rounded-xl font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          <Zap
            className={`relative z-10 ${isAnalyzing ? "animate-spin" : ""}`}
            size={20}
          />
          <span className="relative z-10">
            {isAnalyzing ? "Analyzing..." : "Run New Analysis"}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("map")}
          className="flex items-center gap-2 bg-slate-800 text-white px-8 py-4 rounded-xl font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all"
        >
          <Map size={20} />
          View Risk Map
        </button>
        <button
          onClick={fetchStats}
          className="flex items-center gap-2 bg-slate-800 text-white px-6 py-4 rounded-xl font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all"
        >
          <RefreshCw size={20} />
        </button>
      </div>

      <div>
        <h2 className="text-3xl font-bold text-white mb-2">Mission Snapshot</h2>
        <p className="text-gray-400 mb-6">
          Real-time metrics from the latest orbital sweep
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="group relative bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-cyan-500/50 transition-all overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-cyan-500/10 rounded-lg">
                  <Satellite className="text-cyan-400" size={24} />
                </div>
                <div className="text-gray-400 text-sm">Satellites Tracked</div>
              </div>
              <div className="text-4xl font-bold text-white mb-1">
                {stats.totalSatellites}
              </div>
              <div className="text-cyan-400 text-xs font-medium">
                +12 from last sweep
              </div>
            </div>
          </div>

          <div className="group relative bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-blue-500/50 transition-all overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  <Activity className="text-blue-400" size={24} />
                </div>
                <div className="text-gray-400 text-sm">Close Approaches</div>
              </div>
              <div className="text-4xl font-bold text-white mb-1">
                {stats.closeApproaches}
              </div>
              <div className="text-blue-400 text-xs font-medium">
                Within 100km threshold
              </div>
            </div>
          </div>

          <div className="group relative bg-gradient-to-br from-red-950/50 to-slate-900 p-6 rounded-xl border border-red-700/50 hover:border-red-500/70 transition-all overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-red-500/20 rounded-lg animate-pulse">
                  <AlertTriangle className="text-red-400" size={24} />
                </div>
                <div className="text-gray-300 text-sm">Critical Events</div>
              </div>
              <div className="text-4xl font-bold text-white mb-1">
                {stats.highRiskEvents}
              </div>
              <div className="text-red-400 text-xs font-medium">
                Requires immediate action
              </div>
            </div>
          </div>

          <div className="group relative bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-700 hover:border-purple-500/50 transition-all overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Clock className="text-purple-400" size={24} />
                </div>
                <div className="text-gray-400 text-sm">Last Analysis</div>
              </div>
              <div className="text-lg font-bold text-white mb-1">
                {stats.lastAnalysis || "Never"}
              </div>
              <div className="text-purple-400 text-xs font-medium">
                UTC timestamp
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-cyan-500/20 shadow-xl">
        <div className="flex items-start gap-4 mb-4">
          <div className="p-3 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-xl">
            <Brain className="text-cyan-400" size={28} />
          </div>
          <div className="flex-1">
            <div className="text-white font-bold text-lg mb-1">
              Live AI Orchestration Pipeline
            </div>
            <div className="text-cyan-400 text-sm font-medium mb-2">
              Model A → B → C → D
            </div>
            <p className="text-gray-400 text-sm">
              Real-time orbit propagation, heuristic risk scoring, multi-LLM
              maneuver negotiation, and automated report generation
            </p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 mt-4">
          {[
            { model: "A", name: "Orbit Engine", icon: Database, color: "cyan" },
            {
              model: "B",
              name: "Risk Predictor",
              icon: Activity,
              color: "blue",
            },
            {
              model: "C",
              name: "LLM Negotiator",
              icon: Brain,
              color: "purple",
            },
            { model: "D", name: "Report Gen", icon: FileText, color: "pink" },
          ].map(({ model, name, icon: Icon, color }) => (
            <div
              key={model}
              className={`bg-slate-800/50 p-4 rounded-lg border border-${color}-500/30 hover:border-${color}-500/60 transition-all group cursor-pointer`}
            >
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`text-${color}-400`} size={18} />
                <span className={`text-${color}-400 font-bold`}>
                  Model {model}
                </span>
              </div>
              <div className="text-gray-400 text-xs">{name}</div>
              <div
                className={`mt-2 w-full h-1 bg-slate-700 rounded-full overflow-hidden`}
              >
                <div
                  className={`h-full bg-gradient-to-r from-${color}-500 to-${color}-400 animate-pulse`}
                  style={{ width: "100%" }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const TLEUploadView = () => (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2">
          TLE Upload + Processing
        </h1>
        <p className="text-gray-400 text-lg">
          Upload orbital element data and watch Model A propagate in real-time
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-8 rounded-xl border-2 border-dashed border-cyan-500/30 hover:border-cyan-500/60 transition-all group">
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="p-6 bg-cyan-500/10 rounded-2xl group-hover:scale-110 transition-transform">
              <Upload className="text-cyan-400" size={48} />
            </div>
            <h3 className="text-xl font-semibold text-white">
              Drop TLE files or paste raw text
            </h3>
            <p className="text-gray-400 text-center max-w-md">
              Streams to Model A orbit propagator with SGP4. Real-time
              processing logs below.
            </p>
            <div className="flex gap-3">
              <label className="cursor-pointer bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-8 py-3 rounded-xl font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all">
                <input
                  type="file"
                  className="hidden"
                  accept=".tle,.txt"
                  onChange={handleFileUpload}
                  disabled={isProcessing}
                />
                {isProcessing ? "Processing..." : "Upload & Process"}
              </label>
              <button className="bg-slate-800 text-white px-8 py-3 rounded-xl font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all">
                Paste TLE
              </button>
            </div>
            {isProcessing && (
              <div className="w-full mt-4">
                <div className="bg-slate-800 rounded-full h-3 overflow-hidden border border-cyan-500/30">
                  <div
                    className="bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 h-full transition-all duration-300 animate-pulse"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-center text-cyan-400 text-sm mt-2 font-medium">
                  Processing TLE data... {uploadProgress}%
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Cpu className="text-cyan-400" size={20} />
                Orbit Engine Logs
              </h3>
              <p className="text-gray-400 text-sm">Live stream from Model A</p>
            </div>
            {logs.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/30">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 text-xs font-medium">
                  ACTIVE
                </span>
              </div>
            )}
          </div>
          <div className="bg-slate-950 rounded-lg p-4 h-64 overflow-y-auto border border-slate-800 custom-scrollbar">
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Database className="mx-auto mb-2 opacity-50" size={32} />
                  <p className="text-sm">Waiting for TLE upload...</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2 font-mono text-xs">
                {logs.map((log, i) => (
                  <div
                    key={i}
                    className="text-gray-300 bg-slate-900/50 p-2 rounded animate-slideIn border-l-2 border-cyan-500/50"
                  >
                    <span className="text-cyan-400">
                      [{new Date().toLocaleTimeString()}]
                    </span>{" "}
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-6 border-b border-slate-700 bg-slate-900/50">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Satellite className="text-cyan-400" size={24} />
            Tracked Satellites
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Parsed from uploaded TLE data
          </p>
        </div>
        <div className="overflow-x-auto">
          {satellites.length === 0 ? (
            <div className="p-12 text-center">
              <Satellite className="mx-auto mb-4 text-gray-600" size={48} />
              <p className="text-gray-500">
                No satellites loaded. Upload TLE files to begin.
              </p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-slate-950">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-medium text-cyan-400">
                    Name
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-cyan-400">
                    Inclination
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-cyan-400">
                    Period
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-cyan-400">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {satellites.map((sat, i) => (
                  <tr
                    key={i}
                    className="hover:bg-slate-800/50 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm text-white font-medium">
                      {sat.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300">
                      {sat.inclination}°
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300">
                      {sat.period}m
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-medium border border-green-500/30">
                        {sat.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );

  const CollisionMapView = () => (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2">
          Collision Risk Map
        </h1>
        <p className="text-gray-400 text-lg">
          Live orbital graph with conjunction analysis from Models A & B
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-slate-700 p-6 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Map className="text-cyan-400" size={20} />
              Orbital Graph Visualization
            </h3>
            <button
              onClick={fetchOrbitData}
              className="flex items-center gap-2 bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
          <canvas
            ref={canvasRef}
            className="w-full h-96 rounded-lg bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-800"
          />
          <p className="text-gray-500 text-xs mt-3 text-center">
            Real-time propagation • Nodes: satellites • Edges: close approaches
            color-coded by risk
          </p>
        </div>

        <div className="space-y-4">
          {selectedPair || (riskPairs.length > 0 && riskPairs[0]) ? (
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="text-red-400" size={20} />
                High-Risk Conjunction
              </h3>

              {(() => {
                const pair = selectedPair || riskPairs[0];
                return (
                  <>
                    <div className="mb-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium border ${
                          pair.severity === "high"
                            ? "bg-red-500/20 text-red-400 border-red-500/30"
                            : pair.severity === "medium"
                            ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                            : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                        }`}
                      >
                        {pair.severity}
                      </span>
                      <span className="text-gray-400 text-sm ml-2">
                        Risk: {pair.riskScore}
                      </span>
                    </div>

                    <div className="text-2xl font-bold text-white mb-4">
                      {pair.sat1} ↔ {pair.sat2}
                    </div>

                    <div className="space-y-2 text-sm mb-4 bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Min distance:</span>
                        <span className="text-cyan-400 font-bold">
                          {pair.minDistance} km
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-300 text-sm mb-4 leading-relaxed">
                      {pair.description}
                    </p>

                    <div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-4 rounded-lg border border-cyan-500/30 mb-4">
                      <div className="text-cyan-400 text-xs font-medium mb-2">
                        RECOMMENDED MANEUVER (Model C)
                      </div>
                      <div className="text-white text-sm">{pair.maneuver}</div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() =>
                          simulateManeuver(
                            pair.sat1,
                            pair.sat2,
                            pair.minDistance
                          )
                        }
                        className="flex-1 bg-slate-800 text-white px-4 py-3 rounded-lg font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all flex items-center justify-center gap-2"
                      >
                        <Play size={16} />
                        Simulate
                      </button>
                      <button className="flex-1 bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-4 py-3 rounded-lg font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all">
                        Apply Plan
                      </button>
                    </div>
                  </>
                );
              })()}
            </div>
          ) : null}

          <button
            onClick={fetchOrbitData}
            className="w-full bg-gradient-to-r from-slate-800 to-slate-700 text-white px-4 py-3 rounded-lg font-medium hover:from-slate-700 hover:to-slate-600 border border-slate-600 hover:border-cyan-500/50 transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw size={18} />
            Refresh Graph
          </button>
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-6 border-b border-slate-700 bg-slate-900/50">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="text-cyan-400" size={24} />
            All Conjunctions
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Risk-scored by Model B • Click to view details
          </p>
        </div>
        <div className="p-6">
          {riskPairs.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="mx-auto mb-4 text-gray-600" size={48} />
              <p className="text-gray-500">
                No conjunctions detected. Run analysis to identify close
                approaches.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {riskPairs.map((pair, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedPair(pair)}
                  className={`bg-slate-950 p-5 rounded-lg border transition-all cursor-pointer ${
                    selectedPair === pair
                      ? "border-cyan-500 shadow-lg shadow-cyan-500/20"
                      : "border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium border ${
                        pair.severity === "high"
                          ? "bg-red-500/20 text-red-400 border-red-500/30 animate-pulse"
                          : pair.severity === "medium"
                          ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                          : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                      }`}
                    >
                      {pair.severity}
                    </span>
                    <span className="text-cyan-400 text-xs font-bold">
                      {pair.minDistance} km
                    </span>
                  </div>
                  <div className="text-white font-medium text-sm mb-2">
                    {pair.sat1} ↔ {pair.sat2}
                  </div>
                  <div className="text-gray-400 text-xs">
                    Risk score: {pair.riskScore}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const ReportsView = () => (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2">
          Mission Reports
        </h1>
        <p className="text-gray-400 text-lg">
          AI-generated summaries from Model D with export capabilities
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
            <FileText className="text-cyan-400" size={20} />
            Latest Mission Brief
          </h2>
          <p className="text-gray-400 text-sm mb-4">
            Generated by Model D (Gemini)
          </p>
          <p className="text-gray-300 mb-6 leading-relaxed">
            Automated report includes executive summary, high-risk encounters,
            recommended maneuvers, and safety protocols. Data sourced from
            Models A-C pipeline.
          </p>
          <div className="flex gap-3">
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all"
            >
              <Download size={20} />
              Download PDF
            </button>
            <button className="flex items-center gap-2 bg-slate-800 text-white px-6 py-3 rounded-xl font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all">
              <FileText size={20} />
              Print
            </button>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="text-cyan-400" size={20} />
            Report Metadata
          </h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-gray-400">Objects</span>
              <span className="text-white font-medium">
                {stats.totalSatellites}
              </span>
            </div>
            <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-gray-400">Conjunctions</span>
              <span className="text-white font-medium">{riskPairs.length}</span>
            </div>
            <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-gray-400">Last Generated</span>
              <span className="text-cyan-400 font-medium">
                {stats.lastAnalysis || "Never"}
              </span>
            </div>
            <div className="flex justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-gray-400">Status</span>
              <span className="text-green-400 font-medium flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                Ready
              </span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-white mb-2">
          Risks + Maneuvers
        </h2>
        <p className="text-gray-400 mb-4">
          Model C multi-LLM negotiation results ready for export
        </p>

        <div className="space-y-4">
          {riskPairs.length === 0 ? (
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-12 rounded-xl border border-slate-700 text-center">
              <FileText className="mx-auto mb-4 text-gray-600" size={48} />
              <p className="text-gray-500">
                No risk data available. Run analysis to generate reports.
              </p>
            </div>
          ) : (
            riskPairs.map((pair, i) => (
              <div
                key={i}
                className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-slate-700 hover:border-cyan-500/50 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-bold text-white">
                        {pair.sat1} ↔ {pair.sat2}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium border ${
                          pair.severity === "high"
                            ? "bg-red-500/20 text-red-400 border-red-500/30"
                            : pair.severity === "medium"
                            ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                            : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                        }`}
                      >
                        {pair.severity}
                      </span>
                    </div>
                    <div className="text-sm text-gray-400 mb-3">
                      Risk score{" "}
                      <span className="font-bold text-cyan-400">
                        {pair.riskScore}
                      </span>{" "}
                      • Min distance{" "}
                      <span className="font-bold text-cyan-400">
                        {pair.minDistance} km
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm leading-relaxed">
                      {pair.description}
                    </p>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-4 rounded-lg border border-cyan-500/30">
                  <div className="text-cyan-400 text-xs font-medium mb-2 flex items-center gap-2">
                    <Brain size={14} />
                    LLM-NEGOTIATED MANEUVER
                  </div>
                  <div className="text-white text-sm">{pair.maneuver}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-xl border border-cyan-500/20">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Send className="text-cyan-400" size={20} />
          Export Channels
        </h2>
        <p className="text-gray-400 text-sm mb-4">
          Configure delivery per constellation or mission team
        </p>
        <div className="flex flex-wrap gap-3">
          <button className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all">
            <Send size={18} />
            Send to Mission Control
          </button>
          <button className="flex items-center gap-2 bg-slate-800 text-white px-6 py-3 rounded-xl font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all">
            <Database size={18} />
            Sync to S3
          </button>
          <button className="flex items-center gap-2 bg-slate-800 text-white px-6 py-3 rounded-xl font-medium hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all">
            <FileText size={18} />
            Email PDF
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-10px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0f172a;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
      `}</style>

      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-cyan-500 to-blue-600 p-2.5 rounded-xl shadow-lg shadow-cyan-500/50">
                <Satellite className="text-white" size={26} />
              </div>
              <div>
                <div className="text-xs text-cyan-400 font-medium tracking-wider">
                  ORBITAL GUARDIAN
                </div>
                <div className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  Space Debris Intelligence
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 text-sm font-medium">
                  System Online
                </span>
              </div>
              <button className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2">
                <Brain size={18} />
                Multi-LLM
              </button>
            </div>
          </div>
        </div>
      </header>

      <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-xl sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            {[
              { id: "dashboard", label: "Dashboard", icon: Activity },
              { id: "upload", label: "TLE Upload", icon: Upload },
              { id: "map", label: "Collision Map", icon: Map },
              { id: "reports", label: "Mission Reports", icon: FileText },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 font-medium transition-all border-b-2 relative ${
                  activeTab === tab.id
                    ? "text-cyan-400 border-cyan-400 bg-slate-800/50"
                    : "text-gray-400 border-transparent hover:text-white hover:bg-slate-800/30"
                }`}
              >
                {activeTab === tab.id && (
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-blue-500/5" />
                )}
                <tab.icon size={18} className="relative z-10" />
                <span className="relative z-10">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === "dashboard" && <DashboardView />}
        {activeTab === "upload" && <TLEUploadView />}
        {activeTab === "map" && <CollisionMapView />}
        {activeTab === "reports" && <ReportsView />}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/50 backdrop-blur-xl mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>© 2025 Orbital Guardian • Multi-LLM Space Intelligence</div>
            <div className="flex items-center gap-4">
              <span>
                Models: A (SGP4) • B (Heuristic) • C (Gemini) • D (Gemini)
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default OrbitalGuardian;
