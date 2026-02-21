import { useState } from "react";
import { RAG_BASE } from "./config";

interface Props {
  onAuth: () => void;
}

export default function Login({ onAuth }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = async () => {
    const endpoint =
      mode === "login"
        ? `${RAG_BASE}/auth/login`
        : `${RAG_BASE}/auth/register`;

    const body =
      mode === "login"
        ? { email, password }
        : { username, email, password };

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!data.success) {
      alert("Authentication failed");
      return;
    }

    localStorage.setItem("token", data.token);
    onAuth();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white">

      <div className="w-[420px] border border-purple-500/40 bg-[#0e1420] rounded-xl p-8">

        <h1 className="text-xl tracking-[0.3em] text-purple-400 mb-6 text-center">
          DIGITAL MEMORY TWIN
        </h1>

        {mode === "register" && (
          <input
            placeholder="Username"
            className="w-full mb-4 p-3 bg-[#111827] rounded"
            onChange={(e) => setUsername(e.target.value)}
          />
        )}

        <input
          placeholder="Email"
          className="w-full mb-4 p-3 bg-[#111827] rounded"
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full mb-6 p-3 bg-[#111827] rounded"
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={submit}
          className="w-full py-2 border border-purple-500 text-purple-400 rounded hover:bg-purple-500/20"
        >
          {mode === "login" ? "LOGIN" : "REGISTER"}
        </button>

        <div className="mt-6 text-center text-sm text-gray-400">
          {mode === "login" ? "No account?" : "Already have account?"}
          <button
            onClick={() =>
              setMode(mode === "login" ? "register" : "login")
            }
            className="ml-2 text-purple-400"
          >
            {mode === "login" ? "Register" : "Login"}
          </button>
        </div>
      </div>
    </div>
  );
}