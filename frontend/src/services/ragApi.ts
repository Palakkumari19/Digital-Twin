import axios from "axios";
import { RAG_BASE } from "../config";

export const uploadPDF = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await axios.post(
    `${RAG_BASE}/upload-pdf`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );

  return res.data;
};

export const createSession = async (documentId: string) => {
  const res = await axios.post(
    `${RAG_BASE}/sessions/create`,
    {
      title: "Document Session",
      document_id: documentId,
      document_url: documentId
    }
  );

  return res.data;
};

export const askRag = async (
  question: string,
  sessionId: string
) => {
  const formData = new FormData();
  formData.append("question", question);
  formData.append("session_id", sessionId);

  const res = await axios.post(
    `${RAG_BASE}/chat`,
    formData
  );

  return res.data;
};