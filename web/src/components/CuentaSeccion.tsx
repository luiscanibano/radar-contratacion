import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlanUpgrade } from "@/components/PlanUpgrade";
import {
  ApiError,
  SesionCaducadaError,
  abrirPortal,
  miPlan,
  obtenerTokenMcp,
  type InfoPlan,
} from "@/lib/api";

function configMcp(token: string): string {
  return `{
  "mcpServers": {
    "radar-contratacion": {
      "type": "http",
      "url": "https://radarcontratacion.com/mcp",
      "headers": { "Authorization": "Bearer ${token}" }
    }
  }
}`;
}

function BloquePlan({ plan, error }: { plan: InfoPlan | null; error: string }) {
  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!plan) return <p className="text-sm text-muted-foreground">Cargando…</p>;

  return (
    <p className="text-sm">
      Plan <span className="font-medium capitalize">{plan.plan}</span>
      {plan.cuota === null ? (
        <span className="text-muted-foreground"> · sin límite de preguntas</span>
      ) : (
        <span className="text-muted-foreground">
          {" "}
          · {plan.usadas} de {plan.cuota} preguntas usadas este mes
        </span>
      )}
    </p>
  );
}

function BotonPortal({ plan }: { plan: InfoPlan | null }) {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  if (!plan || plan.plan === "free") return null;

  async function abrir() {
    setError("");
    setCargando(true);
    try {
      const url = await abrirPortal();
      window.location.href = url;
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
      setCargando(false);
    }
  }

  return (
    <div className="space-y-2">
      <Button type="button" variant="outline" onClick={abrir} disabled={cargando} className="rounded-full">
        {cargando ? "Abriendo…" : "Gestionar suscripción"}
      </Button>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}

function BloqueToken() {
  // La sesión de la web vive en una cookie httpOnly (no la puede leer JS), así
  // que el token para MCP ya no se "lee" de ningún sitio — se pide bajo
  // demanda a /auth/mcp-token y solo vive en memoria hasta que se copia.
  const [token, setToken] = useState<string | null>(null);
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState("");
  const [copiado, setCopiado] = useState<"config" | "token" | null>(null);

  async function generar() {
    setError("");
    setGenerando(true);
    try {
      setToken(await obtenerTokenMcp());
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "No se pudo generar el token.");
    } finally {
      setGenerando(false);
    }
  }

  async function copiar(texto: string, cual: "config" | "token") {
    try {
      await navigator.clipboard.writeText(texto);
    } catch {
      return;
    }
    setCopiado(cual);
    setTimeout(() => setCopiado(null), 2000);
  }

  if (!token) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Genera un token para conectar Claude, u otro cliente MCP, a{" "}
          <code className="font-mono text-xs">https://radarcontratacion.com/mcp</code>. Caduca a
          los 7 días; genera uno nuevo cuando lo necesites.
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="rounded-full"
          onClick={generar}
          disabled={generando}
        >
          {generando ? "Generando…" : "Generar token"}
        </Button>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Cópialo ahora: no se vuelve a mostrar. Si lo pierdes, genera uno nuevo.
      </p>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="rounded-full"
          onClick={() => copiar(configMcp(token), "config")}
        >
          {copiado === "config" ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
          Copiar configuración
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="rounded-full"
          onClick={() => copiar(token, "token")}
        >
          {copiado === "token" ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
          Copiar solo el token
        </Button>
      </div>
      <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-[#0b1220] p-5 font-mono text-[0.8rem] leading-relaxed text-[#e7ecf5]">
        <code>{configMcp(token)}</code>
      </pre>
    </div>
  );
}

export function CuentaSeccion({ onSalir }: { onSalir: () => void }) {
  const [plan, setPlan] = useState<InfoPlan | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    miPlan()
      .then(setPlan)
      .catch((err) => {
        if (err instanceof SesionCaducadaError) return;
        setError(err instanceof ApiError ? err.message : "No se pudo cargar tu plan.");
      });
  }, []);

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Tu plan
        </h2>
        <div className="mt-4 space-y-4">
          <BloquePlan plan={plan} error={error} />
          <BotonPortal plan={plan} />
        </div>
      </section>

      <PlanUpgrade />

      <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Token para MCP
        </h2>
        <div className="mt-4">
          <BloqueToken />
        </div>
      </section>

      <div>
        <Button type="button" variant="outline" onClick={onSalir} className="rounded-full">
          Salir
        </Button>
      </div>
    </div>
  );
}
