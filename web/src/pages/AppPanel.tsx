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
import {
  ApiError,
  EVENTO_SESION_CADUCADA,
  clearToken,
  crearCheckout,
  getToken,
  quienSoy,
} from "@/lib/api";
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

export function AppPanel() {
  const [vista, setVista] = useState<Vista>({ estado: "cargando" });
  const [seccion, setSeccion] = useState<Seccion>(seccionDesdeHash);
  const [planPendiente] = useState<PlanPendiente | null>(leerPlanPendiente);
  const [errorCheckout, setErrorCheckout] = useState("");
  const checkoutLanzado = useRef(false);

  async function comprobarSesion() {
    if (!getToken()) {
      setVista({ estado: "auth" });
      return;
    }
    try {
      const yo = await quienSoy();
      setVista({ estado: "panel", email: yo.email });
    } catch {
      clearToken();
      setVista({ estado: "auth" });
    }
  }

  useEffect(() => {
    comprobarSesion();
    // Limpia el ?plan= de la URL en cuanto lo hemos leído: no debe sobrevivir
    // a un F5 ni relanzar el checkout si el usuario vuelve atrás.
    if (planPendiente) {
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
    clearToken();
    setVista({ estado: "auth" });
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
