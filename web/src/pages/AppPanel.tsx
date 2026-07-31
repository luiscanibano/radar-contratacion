import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Container } from "@/components/Container";
import { AppTopBar } from "@/components/AppTopBar";
import { AuthCard } from "@/components/AuthCard";
import { AskAgent } from "@/components/AskAgent";
import { AlertsManager } from "@/components/AlertsManager";
import { BuscadorLicitaciones } from "@/components/BuscadorLicitaciones";
import { CuentaSeccion } from "@/components/CuentaSeccion";
import { Button } from "@/components/ui/button";
import { ApiError, EVENTO_SESION_CADUCADA, crearCheckout, logout, quienSoy } from "@/lib/api";
import { cn } from "@/lib/utils";

type Seccion = "preguntar" | "buscar" | "alertas" | "cuenta";
const SECCIONES: { id: Seccion; etiqueta: string }[] = [
  { id: "preguntar", etiqueta: "Preguntar" },
  { id: "buscar", etiqueta: "Buscar" },
  { id: "alertas", etiqueta: "Alertas" },
  { id: "cuenta", etiqueta: "Cuenta" },
];

function seccionDesdeHash(): Seccion {
  const hash = location.hash.slice(1);
  return (SECCIONES.find((s) => s.id === hash)?.id ?? "preguntar") as Seccion;
}

type Vista = { estado: "cargando" } | { estado: "auth"; aviso?: string } | { estado: "panel"; email: string };
type PlanPendiente = "basico" | "pro" | "ilimitado";

function leerPlanPendiente(): PlanPendiente | null {
  const plan = new URLSearchParams(location.search).get("plan");
  return plan === "basico" || plan === "pro" || plan === "ilimitado" ? plan : null;
}

/** `?verificado=1|0`, puesto por el redirect de GET /auth/verificar (ver
 * api/main.py): 1 si el enlace del email era válido, 0 si estaba caducado o
 * ya se había usado. */
function leerVerificado(): "1" | "0" | null {
  const v = new URLSearchParams(location.search).get("verificado");
  return v === "1" || v === "0" ? v : null;
}

/** `?reset_token=...`, el enlace del email de "olvidé mi contraseña" (ver
 * /auth/olvide-password): fuerza el formulario de contraseña nueva aunque ya
 * haya una sesión abierta. */
function leerResetToken(): string | null {
  return new URLSearchParams(location.search).get("reset_token");
}

export function AppPanel() {
  const [vista, setVista] = useState<Vista>({ estado: "cargando" });
  const [seccion, setSeccion] = useState<Seccion>(seccionDesdeHash);
  const [planPendiente] = useState<PlanPendiente | null>(leerPlanPendiente);
  const [verificado] = useState<"1" | "0" | null>(leerVerificado);
  const [resetToken] = useState<string | null>(leerResetToken);
  const [errorCheckout, setErrorCheckout] = useState("");
  const checkoutLanzado = useRef(false);

  async function comprobarSesion() {
    // La sesión vive en una cookie httpOnly: no hay nada que comprobar en el
    // cliente, hay que preguntarle a la API si la cookie (si existe) es válida.
    try {
      const yo = await quienSoy();
      setVista({ estado: "panel", email: yo.email });
    } catch {
      setVista({
        estado: "auth",
        aviso: verificado === "0" ? "El enlace de confirmación no es válido o ha caducado." : undefined,
      });
    }
  }

  useEffect(() => {
    // Con un token de reset en la URL, el formulario de contraseña nueva
    // tiene prioridad sobre cualquier sesión ya abierta: no tiene sentido
    // esperar a comprobarSesion (que llevaría directo al panel) si el
    // usuario ha llegado aquí explícitamente para cambiar su contraseña.
    if (resetToken) {
      setVista({ estado: "auth" });
    } else {
      comprobarSesion();
    }
    // Limpia ?plan=/?verificado=/?reset_token= de la URL en cuanto los hemos
    // leído: no deben sobrevivir a un F5 ni (en el caso del token) quedar
    // colgados en el historial del navegador.
    if (planPendiente || verificado || resetToken) {
      history.replaceState(null, "", location.pathname + location.hash);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    function onHashChange() {
      setSeccion(seccionDesdeHash());
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    function onSesionCaducada() {
      setVista({ estado: "auth", aviso: "Tu sesión ha caducado. Vuelve a iniciar sesión." });
    }
    window.addEventListener(EVENTO_SESION_CADUCADA, onSesionCaducada);
    return () => window.removeEventListener(EVENTO_SESION_CADUCADA, onSesionCaducada);
  }, []);

  useEffect(() => {
    if (vista.estado !== "panel" || !planPendiente || checkoutLanzado.current) return;
    checkoutLanzado.current = true;
    crearCheckout(planPendiente)
      .then((url) => {
        window.location.href = url;
      })
      .catch((err) => {
        setErrorCheckout(
          err instanceof ApiError ? err.message : "No se pudo iniciar el pago del plan elegido.",
        );
        location.hash = "cuenta";
      });
  }, [vista, planPendiente]);

  function irA(s: Seccion) {
    setSeccion(s);
    location.hash = s;
  }

  function salir() {
    logout().finally(() => setVista({ estado: "auth" }));
  }

  return (
    <div className="min-h-screen bg-background">
      <Container size="narrow">
        <AppTopBar email={vista.estado === "panel" ? vista.email : undefined} onSalir={salir} />

        <main className="py-12">
          <AnimatePresence mode="wait">
            {vista.estado === "auth" && (
              <motion.div key="auth" exit={{ opacity: 0 }}>
                <AuthCard
                  registroInicial={location.hash === "#registro" || planPendiente !== null}
                  resetToken={resetToken ?? undefined}
                  aviso={vista.aviso}
                  onAutenticado={comprobarSesion}
                />
              </motion.div>
            )}
            {vista.estado === "panel" && (
              <motion.div
                key="panel"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                {verificado === "1" && (
                  <p className="text-sm text-emerald-600">Cuenta confirmada. ¡Bienvenido!</p>
                )}
                {errorCheckout && <p className="text-sm text-destructive">{errorCheckout}</p>}
                <nav className="flex flex-wrap gap-2">
                  {SECCIONES.map((s) => (
                    <Button
                      key={s.id}
                      type="button"
                      size="sm"
                      variant={seccion === s.id ? "secondary" : "ghost"}
                      onClick={() => irA(s.id)}
                      className={cn("rounded-full", seccion === s.id && "font-medium")}
                    >
                      {s.etiqueta}
                    </Button>
                  ))}
                </nav>

                {seccion === "preguntar" && <AskAgent />}
                {seccion === "buscar" && <BuscadorLicitaciones />}
                {seccion === "alertas" && <AlertsManager />}
                {seccion === "cuenta" && <CuentaSeccion onSalir={salir} />}
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </Container>
    </div>
  );
}
