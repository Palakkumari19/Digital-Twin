import { useState } from "react";
import axios from "axios";
import ForceGraph2D from "react-force-graph-2d";

const SIMPLE_BASE = "http://127.0.0.1:8000/simple";
const RAG_BASE = "http://127.0.0.1:8000/rag/api/v1";

export default function App() {
  const [mode, setMode] = useState<"simple" | "rag">("simple");

  const [text, setText] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [graphData, setGraphData] = useState<any>(null);
  const [ragGraph, setRagGraph] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());

  // ================= SIMPLE =================

  const uploadNotes = async () => {
    if (!text.trim()) return alert("Enter notes first");
    await axios.post(`${SIMPLE_BASE}/upload`, { text });
    alert("Notes uploaded ✅");
    setText("");
  };

  const loadGraph = async () => {
    const res = await axios.get(`${SIMPLE_BASE}/graph`);
    setGraphData({
      nodes: res.data.nodes,
      links: res.data.edges,
    });
  };

  // ================= RAG =================

  const uploadPDF = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await axios.post(
      `${RAG_BASE}/upload-pdf`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );

    const docId = uploadRes.data.file_id;

    const sessionRes = await axios.post(
      `${RAG_BASE}/sessions/create`,
      {
        title: "Document Session",
        document_id: docId,
        document_url: docId,
      }
    );

    setSessionId(sessionRes.data.session_id);
    alert("Document ready 🚀");
  };

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);

    try {
      if (mode === "simple") {
        const res = await axios.post(`${SIMPLE_BASE}/ask`, {
          question,
        });

        const answerText = res.data.answer;
        setAnswer(answerText);

        // Highlight capitalized entities in simple graph
        // const entities =
        //   answerText.match(/\b[A-Z][a-zA-Z]+\b/g) || [];

        // setHighlightNodes(new Set(entities));
        // Extract keywords from question + answer
        const combinedText = (question + " " + answerText).toLowerCase();

        // If graph is loaded, check which nodes appear in text
        if (graphData?.nodes) {
          const matched = graphData.nodes
            .map((n: any) => n.id)
            .filter((id: string) =>
              combinedText.includes(id.toLowerCase())
            );

          setHighlightNodes(new Set(matched));
        }
      } else {
        if (!sessionId) {
          alert("Upload document first");
          setLoading(false);
          return;
        }

        const formData = new FormData();
        formData.append("question", question);
        formData.append("session_id", sessionId);

        const res = await axios.post(
          `${RAG_BASE}/chat`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );

        const answerText = res.data.answer;
        setAnswer(answerText);

        // Build structured RAG graph
        const entities =
          answerText.match(/\b[A-Z][a-zA-Z]+\b/g) || [];

        const uniqueEntities = [...new Set(entities)];

        const nodes = [
          { id: "Answer", group: 0 },
          ...uniqueEntities.map((e) => ({
            id: e,
            group: 1,
          })),
        ];

        const links = uniqueEntities.map((e) => ({
          source: "Answer",
          target: e,
        }));

        setRagGraph({ nodes, links });
      }
    } catch (err: any) {
      console.error(err.response?.data || err);
      alert("Something went wrong. Check backend logs.");
    }

    setLoading(false);
  };

  // ================= UI =================

  return (
    <div className="min-h-screen bg-[#0b0f17] text-white px-16 py-10">
      {/* HEADER */}
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-3xl tracking-[0.3em] font-semibold">
            DIGITAL MEMORY TWIN
          </h1>
          <p className="text-xs text-gray-400 tracking-[0.3em] mt-2">
            AI-AUGMENTED KNOWLEDGE INTERFACE
          </p>
        </div>

        <div className="flex gap-6 items-center">
          <button
            onClick={() => setMode("simple")}
            className={`text-sm ${
              mode === "simple" ? "text-cyan-400" : "text-gray-400"
            }`}
          >
            SIMPLE
          </button>

          <button
            onClick={() => setMode("rag")}
            className={`text-sm ${
              mode === "rag" ? "text-purple-400" : "text-gray-400"
            }`}
          >
            ADVANCED
          </button>

          <div className="px-4 py-1 border border-green-400 rounded-full text-xs text-green-400">
            ● SYSTEM ONLINE
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        <div className="space-y-8">
          {/* UPLOAD */}
          <div className="border border-cyan-500/40 rounded-xl p-6 bg-[#111827]">
            <h2 className="text-sm tracking-[0.2em] text-cyan-400 mb-4">
              {mode === "simple" ? "↑ UPLOAD NOTES" : "↑ UPLOAD DOCUMENT"}
            </h2>

            {mode === "simple" ? (
              <>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full h-32 bg-[#1f2937] rounded-lg p-4"
                />
                <button
                  onClick={uploadNotes}
                  className="mt-6 px-6 py-2 border border-cyan-400 text-cyan-400 rounded-lg"
                >
                  UPLOAD
                </button>
              </>
            ) : (
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => {
                  if (e.target.files)
                    uploadPDF(e.target.files[0]);
                }}
              />
            )}
          </div>

          {/* ASK */}
          <div className="border border-purple-500/40 rounded-xl p-6 bg-[#111827]">
            <h2 className="text-sm tracking-[0.2em] text-purple-400 mb-4">
              ⚡ ASK THE MEMORY CORE
            </h2>

            <div className="flex gap-4">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="flex-1 bg-[#1f2937] rounded-lg p-3"
              />
              <button
                onClick={ask}
                className="px-6 py-2 bg-purple-500/20 border border-purple-500 rounded-lg"
              >
                {loading ? "..." : "ASK"}
              </button>
            </div>

            {answer && (
              <div className="mt-6 border border-purple-500/30 rounded-lg p-4 bg-[#1f2937]">
                {answer}
              </div>
            )}
          </div>
        </div>

        {/* GRAPH PANEL */}
        <div className="h-[600px] w-full border border-cyan-500/20 rounded-lg overflow-hidden bg-[#0e1420]">

          {mode === "simple" && (
            <>
              <div className="p-4">
                <button
                  onClick={loadGraph}
                  className="px-4 py-1 border border-cyan-500 rounded-lg text-xs hover:bg-cyan-500/20 transition"
                >
                  INITIALIZE NETWORK
                </button>
              </div>

              {graphData ? (
                <ForceGraph2D
                  graphData={graphData}
                  width={window.innerWidth * 0.45}
                  height={550}
                  backgroundColor="#0e1420"
                  nodeLabel="id"
                  linkColor={() => "#22d3ee"}
                  linkWidth={1.5}
                  linkDirectionalParticles={2}
                  linkDirectionalParticleWidth={2}
                  cooldownTicks={150}
                  d3VelocityDecay={0.3}
                  d3AlphaDecay={0.02}
                  nodeCanvasObject={(node: any, ctx, globalScale) => {
                    const label = node.id;
                    const fontSize = 12 / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;

                    const isHighlighted = highlightNodes.has(node.id);

                    ctx.beginPath();
                    ctx.arc(node.x, node.y, isHighlighted ? 12 : 6, 0, 2 * Math.PI);
                    ctx.fillStyle = isHighlighted ? "#facc15" : "#0891b2";
                    ctx.fill();

                    ctx.fillStyle = isHighlighted ? "#facc15" : "#a5f3fc";
                    ctx.fillText(label, node.x + 8, node.y + 4);
                  }}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                  LOAD GRAPH TO VISUALIZE CONCEPTUAL RELATIONSHIPS
                </div>
              )}
            </>
          )}

          {/* {mode === "rag" && ragGraph && (
            <ForceGraph2D
              graphData={ragGraph}
              width={window.innerWidth * 0.45}
              height={550}
              backgroundColor="#0e1420"
              linkColor={() => "#a855f7"}
              linkDirectionalParticles={3}
              linkDirectionalParticleWidth={2}
              d3VelocityDecay={0.25}
              d3AlphaDecay={0.01}
              d3Force="charge"
              
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.id;
                const fontSize = 13 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;

                ctx.beginPath();
                ctx.arc(node.x, node.y, node.id === "Answer" ? 14 : 4, 0, 2 * Math.PI);
                ctx.fillStyle = node.id === "Answer" ? "#a855f7" : "#22d3ee";
                ctx.fill();

                ctx.fillStyle = "#ffffff";
                ctx.fillText(label, node.x + 8, node.y + 4);
              }}
            />
          )} */}
          {mode === "rag" && ragGraph && (
  <ForceGraph2D
    graphData={ragGraph}
    width={window.innerWidth * 0.45}
    height={550}
    backgroundColor="#0e1420"

    // Better spacing physics
    d3VelocityDecay={0.25}
    d3AlphaDecay={0.01}
    d3Force={(fg) => {
      fg.d3Force("charge")?.strength(-280); // more spread
      fg.d3Force("link")?.distance(120);    // increase distance from center
    }}

    // Link styling
    linkColor={() => "#a855f7"}
    linkWidth={1.2}
    linkDirectionalParticles={2}
    linkDirectionalParticleWidth={2}

    // Custom node rendering
    nodeCanvasObject={(node: any, ctx, globalScale) => {
      const label = node.id;
      const fontSize = 11 / globalScale;
      ctx.font = `${fontSize}px Sans-Serif`;

      const isCenter = node.id === "Answer";

      // Draw node circle
      ctx.beginPath();
      ctx.arc(
        node.x,
        node.y,
        isCenter ? 16 : 4,  // center bigger, outer small
        0,
        2 * Math.PI
      );
      ctx.fillStyle = isCenter ? "#a855f7" : "#22d3ee";
      ctx.fill();

      // Draw label
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, node.x + 6, node.y + 3);
    }}
  />
)}
        </div>
      </div>
    </div>
  );
}