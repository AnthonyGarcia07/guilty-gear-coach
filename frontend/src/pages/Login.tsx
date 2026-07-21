import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { normalizeUnknownError } from "../api/errors";
import { useAuth } from "../auth/AuthContext";

export function Login({ mode }: { mode: "login" | "signup" }) {
  const { user, login, signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "signup") await signup(email, username, password);
      else await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(normalizeUnknownError(err, "Authentication failed").message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <Link to="/" className="mini-brand">Guilty Gear Coach</Link>
        <h1>{mode === "signup" ? "Create your profile" : "Welcome back"}</h1>
        {error && <p className="form-error">{error}</p>}
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        {mode === "signup" && <label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} required minLength={2} /></label>}
        <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} /></label>
        <button className="primary-button" disabled={busy}>{busy ? "Checking..." : mode === "signup" ? "Create account" : "Log in"}</button>
        <p>{mode === "signup" ? "Already tracking matches?" : "Need an account?"} <Link to={mode === "signup" ? "/login" : "/signup"}>{mode === "signup" ? "Log in" : "Sign up"}</Link></p>
      </form>
    </main>
  );
}
