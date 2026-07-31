import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, login, registrar } from "@/lib/api";

export function AuthCard({
  registroInicial = false,
  aviso,
  onAutenticado,
}: {
  registroInicial?: boolean;
  aviso?: string;
  onAutenticado: () => void;
}) {
  const [modoRegistro, setModoRegistro] = useState(registroInicial);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      if (modoRegistro) {
        await registrar({ email, password });
      } else {
        await login({ email, password });
      }
      setPassword("");
      onAutenticado();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto w-full max-w-sm rounded-3xl border border-border bg-card/80 p-8 shadow-xl shadow-black/5 backdrop-blur-sm"
    >
      <h1 className="text-xl font-semibold tracking-tight">
        {modoRegistro ? "Crear cuenta" : "Iniciar sesión"}
      </h1>
      {aviso && <p className="mt-3 text-sm text-amber-600 dark:text-amber-400">{aviso}</p>}
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="auth-email">Email</Label>
          <Input
            id="auth-email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="auth-password">Contraseña</Label>
          <Input
            id="auth-password"
            type="password"
            minLength={8}
            autoComplete={modoRegistro ? "new-password" : "current-password"}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={enviando} className="w-full rounded-full">
          {enviando ? "Comprobando…" : modoRegistro ? "Registrarme" : "Entrar"}
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted-foreground">
        {modoRegistro ? "¿Ya tienes cuenta? " : "¿No tienes cuenta? "}
        <button
          type="button"
          onClick={() => {
            setModoRegistro((v) => !v);
            setError("");
          }}
          className="text-primary underline-offset-4 hover:underline"
        >
          {modoRegistro ? "Inicia sesión" : "Regístrate gratis"}
        </button>
      </p>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
    </motion.div>
  );
}
