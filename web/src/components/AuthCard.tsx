import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  login,
  olvidePassword,
  reenviarVerificacion,
  registrar,
  resetearPassword,
} from "@/lib/api";

type Modo = "login" | "registro" | "registro-enviado" | "olvide" | "olvide-enviado" | "reset";

const TITULOS: Record<Modo, string> = {
  login: "Iniciar sesión",
  registro: "Crear cuenta",
  "registro-enviado": "Revisa tu email",
  olvide: "Recuperar contraseña",
  "olvide-enviado": "Revisa tu email",
  reset: "Elige una contraseña nueva",
};

/** Botón de "reenviar email de confirmación", usado tanto tras el registro
 * como cuando un login falla por email sin verificar. */
function BotonReenviarVerificacion({ email }: { email: string }) {
  const [estado, setEstado] = useState<"idle" | "enviando" | "enviado">("idle");
  const [error, setError] = useState("");

  async function reenviar() {
    setError("");
    setEstado("enviando");
    try {
      await reenviarVerificacion(email);
      setEstado("enviado");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
      setEstado("idle");
    }
  }

  if (estado === "enviado") {
    return <p className="mt-2 text-sm text-muted-foreground">Te hemos reenviado el email.</p>;
  }
  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={reenviar}
        disabled={estado === "enviando"}
        className="text-sm text-primary underline-offset-4 hover:underline"
      >
        {estado === "enviando" ? "Reenviando…" : "Reenviar email de confirmación"}
      </button>
      {error && <p className="mt-1 text-sm text-destructive">{error}</p>}
    </div>
  );
}

export function AuthCard({
  registroInicial = false,
  resetToken,
  aviso,
  onAutenticado,
}: {
  registroInicial?: boolean;
  /** Presente cuando se llega desde el enlace de "olvidé mi contraseña"
   * (?reset_token=... en la URL, ver AppPanel): fuerza el modo "reset". */
  resetToken?: string;
  aviso?: string;
  onAutenticado: () => void;
}) {
  const [modo, setModo] = useState<Modo>(
    resetToken ? "reset" : registroInicial ? "registro" : "login",
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmarPassword, setConfirmarPassword] = useState("");
  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [loginSinVerificar, setLoginSinVerificar] = useState(false);

  // Tanto el registro como el reset fijan una contraseña nueva: un typo deja
  // al usuario con una contraseña que no conoce, así que ambos piden
  // confirmarla.
  const pideConfirmarPassword = modo === "registro" || modo === "reset";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoginSinVerificar(false);

    if (pideConfirmarPassword && password !== confirmarPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (modo === "registro" && !aceptaTerminos) {
      setError("Debes aceptar los términos de uso y la política de privacidad.");
      return;
    }

    setEnviando(true);
    try {
      if (modo === "login") {
        await login({ email, password });
        setPassword("");
        onAutenticado();
      } else if (modo === "registro") {
        const mensajeRegistro = await registrar({
          email,
          password,
          acepta_terminos: aceptaTerminos,
        });
        setPassword("");
        setConfirmarPassword("");
        setMensaje(mensajeRegistro);
        setModo("registro-enviado");
      } else if (modo === "olvide") {
        const mensajeOlvide = await olvidePassword(email);
        setMensaje(mensajeOlvide);
        setModo("olvide-enviado");
      } else if (modo === "reset" && resetToken) {
        await resetearPassword(resetToken, password);
        setPassword("");
        setConfirmarPassword("");
        onAutenticado();
      }
    } catch (err) {
      if (modo === "login" && err instanceof ApiError && err.status === 403) {
        setLoginSinVerificar(true);
      }
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
    } finally {
      setEnviando(false);
    }
  }

  function cambiarModo(nuevo: Modo) {
    setModo(nuevo);
    setError("");
    setLoginSinVerificar(false);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto w-full max-w-sm rounded-3xl border border-border bg-card/80 p-8 shadow-xl shadow-black/5 backdrop-blur-sm"
    >
      <h1 className="text-xl font-semibold tracking-tight">{TITULOS[modo]}</h1>
      {aviso && <p className="mt-3 text-sm text-amber-600">{aviso}</p>}

      {modo === "registro-enviado" || modo === "olvide-enviado" ? (
        <div className="mt-6 space-y-4">
          <p className="text-sm text-muted-foreground">{mensaje}</p>
          {modo === "registro-enviado" && <BotonReenviarVerificacion email={email} />}
          <button
            type="button"
            onClick={() => cambiarModo("login")}
            className="text-sm text-primary underline-offset-4 hover:underline"
          >
            Volver a iniciar sesión
          </button>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          {modo !== "reset" && (
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
          )}
          {modo !== "olvide" && (
            <div className="space-y-1.5">
              <Label htmlFor="auth-password">
                {modo === "reset" ? "Contraseña nueva" : "Contraseña"}
              </Label>
              <Input
                id="auth-password"
                type="password"
                minLength={8}
                autoComplete={modo === "login" ? "current-password" : "new-password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          )}
          {pideConfirmarPassword && (
            <div className="space-y-1.5">
              <Label htmlFor="auth-confirmar-password">Confirmar contraseña</Label>
              <Input
                id="auth-confirmar-password"
                type="password"
                minLength={8}
                autoComplete="new-password"
                required
                value={confirmarPassword}
                onChange={(e) => setConfirmarPassword(e.target.value)}
              />
            </div>
          )}
          {modo === "registro" && (
            <label htmlFor="auth-acepta-terminos" className="flex items-start gap-2 text-sm text-muted-foreground">
              <input
                id="auth-acepta-terminos"
                type="checkbox"
                required
                checked={aceptaTerminos}
                onChange={(e) => setAceptaTerminos(e.target.checked)}
                className="mt-0.5 size-4 shrink-0 rounded border-border text-primary accent-primary"
              />
              <span>
                He leído y acepto los{" "}
                <a
                  href="/legal#terminos"
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary underline-offset-4 hover:underline"
                >
                  términos de uso
                </a>{" "}
                y la{" "}
                <a
                  href="/legal#privacidad"
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary underline-offset-4 hover:underline"
                >
                  política de privacidad
                </a>
                .
              </span>
            </label>
          )}
          <Button type="submit" disabled={enviando} className="w-full rounded-full">
            {enviando
              ? "Comprobando…"
              : modo === "login"
                ? "Entrar"
                : modo === "registro"
                  ? "Registrarme"
                  : modo === "olvide"
                    ? "Enviar enlace"
                    : "Guardar contraseña"}
          </Button>
        </form>
      )}

      {(modo === "login" || modo === "registro") && (
        <p className="mt-4 text-sm text-muted-foreground">
          {modo === "registro" ? "¿Ya tienes cuenta? " : "¿No tienes cuenta? "}
          <button
            type="button"
            onClick={() => cambiarModo(modo === "registro" ? "login" : "registro")}
            className="text-primary underline-offset-4 hover:underline"
          >
            {modo === "registro" ? "Inicia sesión" : "Regístrate gratis"}
          </button>
        </p>
      )}
      {modo === "login" && (
        <p className="mt-2 text-sm">
          <button
            type="button"
            onClick={() => cambiarModo("olvide")}
            className="text-muted-foreground underline-offset-4 hover:underline"
          >
            ¿Olvidaste tu contraseña?
          </button>
        </p>
      )}
      {modo === "olvide" && (
        <p className="mt-4 text-sm text-muted-foreground">
          <button
            type="button"
            onClick={() => cambiarModo("login")}
            className="text-primary underline-offset-4 hover:underline"
          >
            Volver a iniciar sesión
          </button>
        </p>
      )}

      {error && (
        <div className="mt-3">
          <p className="text-sm text-destructive">{error}</p>
          {loginSinVerificar && <BotonReenviarVerificacion email={email} />}
        </div>
      )}
    </motion.div>
  );
}
