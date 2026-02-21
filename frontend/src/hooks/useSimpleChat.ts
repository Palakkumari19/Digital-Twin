import { useState } from "react";
import { uploadSimpleNotes, askSimple, getGraph } from "../services/simpleApi";

export const useSimpleChat = () => {
  const [answer, setAnswer] = useState("");
  const [graphData, setGraphData] = useState<any>(null);

  const upload = async (text: string) => {
    await uploadSimpleNotes(text);
  };

  const ask = async (question: string) => {
    const res = await askSimple(question);
    setAnswer(res.data.answer || res.data.response);
  };

  const loadGraph = async () => {
    const res = await getGraph();
    setGraphData({
      nodes: res.data.nodes,
      links: res.data.edges,
    });
  };

  return { answer, graphData, upload, ask, loadGraph };
};