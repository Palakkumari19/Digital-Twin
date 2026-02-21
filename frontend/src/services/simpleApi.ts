import axios from "axios";
import { SIMPLE_BASE } from "../config";

export const uploadSimpleNotes = (text: string) =>
  axios.post(`${SIMPLE_BASE}/upload`, { text });

export const askSimple = (question: string) =>
  axios.post(`${SIMPLE_BASE}/ask`, { question });

export const getGraph = () =>
  axios.get(`${SIMPLE_BASE}/graph`);