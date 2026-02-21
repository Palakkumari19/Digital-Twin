import { useState } from "react";
import axios from "axios";
import { BASE_URL } from "../config";

const getToken = () => localStorage.getItem("token");

export const useRagChat = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([]);

  const upload = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await axios.post(
      `${BASE_URL}/rag/api/v1/upload-pdf`,
      formData,
      {
        headers: {
          Authorization: `Bearer ${getToken()}`,
          "Content-Type": "multipart/form-data"
        }
      }
    );

    const documentId = uploadRes.data.file_id;

    const sessionRes = await axios.post(
      `${BASE_URL}/rag/api/v1/sessions/create`,
      {
        title: "Document Session",
        document_id: documentId,
        document_url: documentId
      },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );

    setSessionId(sessionRes.data.session_id);
  };

  const ask = async (question: string) => {
    if (!sessionId) throw new Error("Upload document first");

    setMessages((prev) => [...prev, { role: "user", content: question }]);

    const res = await axios.post(
      `${BASE_URL}/rag/api/v1/chat`,
      { question, session_id: sessionId },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );

    const answer =
      res.data.answer || res.data.response || "No answer found";

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: answer }
    ]);
  };

  return { upload, ask, messages, sessionId };
};