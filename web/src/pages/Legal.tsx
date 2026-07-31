import { Brand } from "@/components/Brand";
import { Container } from "@/components/Container";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Separator } from "@/components/ui/separator";

export function Legal() {
  return (
    <div className="min-h-screen bg-background">
      <Container size="narrow">
        <header className="flex items-center justify-between border-b border-border py-5">
          <Brand compact />
          <ThemeToggle />
        </header>

        <main className="space-y-12 py-12 text-sm leading-relaxed text-muted-foreground">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Aviso legal</h1>

          <section id="privacidad" className="scroll-mt-20 space-y-4">
            <h2 className="text-lg font-semibold tracking-tight text-foreground">
              Política de privacidad
            </h2>
            <p>
              <strong className="text-foreground">Responsable del tratamiento.</strong> Luis
              Cañibano Mateos, contacto:{" "}
              <a
                href="mailto:luiscanibanomateos@gmail.com"
                className="text-primary underline-offset-4 hover:underline"
              >
                luiscanibanomateos@gmail.com
              </a>
              .
            </p>
            <p>
              <strong className="text-foreground">Datos tratados.</strong> Email, contraseña
              cifrada (Argon2, nunca en texto plano), el número de preguntas realizadas al agente
              cada mes, y los datos de tu suscripción (plan, estado y fechas) si te suscribes a un
              plan de pago.
            </p>
            <p>
              <strong className="text-foreground">Finalidad y base legal.</strong> Prestar el
              servicio contratado (ejecución de un contrato) y, en el caso de las alertas por
              email, nuestro interés legítimo en avisarte de las licitaciones que has decidido
              vigilar.
            </p>
            <p>
              <strong className="text-foreground">Encargados de tratamiento.</strong> Stripe
              (pagos y facturación), Resend (envío de los emails de alertas) y Anthropic
              (procesado de las preguntas que le haces al agente conversacional). El servicio se
              aloja en un proveedor de hosting que también actúa como encargado.
            </p>
            <p>
              <strong className="text-foreground">Conservación.</strong> Tus datos se conservan
              mientras tu cuenta esté activa. Puedes solicitar el borrado completo escribiendo al
              email de contacto.
            </p>
            <p>
              <strong className="text-foreground">Tus derechos.</strong> Acceso, rectificación,
              supresión, oposición, limitación y portabilidad. Puedes ejercerlos en cualquier
              momento escribiendo a{" "}
              <a
                href="mailto:luiscanibanomateos@gmail.com"
                className="text-primary underline-offset-4 hover:underline"
              >
                luiscanibanomateos@gmail.com
              </a>
              .
            </p>
          </section>

          <Separator />

          <section id="terminos" className="scroll-mt-20 space-y-4">
            <h2 className="text-lg font-semibold tracking-tight text-foreground">
              Términos de uso
            </h2>
            <p>
              <strong className="text-foreground">El servicio.</strong> Este servicio usa
              exclusivamente datos abiertos oficiales de la Plataforma de Contratación del Sector
              Público. El análisis se presenta de forma agregada y las señales de riesgo describen
              patrones estadísticos a revisar, nunca acusaciones.
            </p>
            <p>
              <strong className="text-foreground">Planes y facturación.</strong> Los planes de
              pago no tienen permanencia. Puedes cambiar de plan o cancelar tu suscripción en
              cualquier momento desde la sección Cuenta del panel, que abre el portal de gestión
              de Stripe.
            </p>
            <p>
              <strong className="text-foreground">Limitación de responsabilidad.</strong> Los
              datos proceden de fuentes públicas oficiales pero pueden contener errores o estar
              desactualizados. El servicio no constituye asesoramiento legal y no debe usarse como
              única fuente para decisiones de contratación.
            </p>
            <p>
              <strong className="text-foreground">Uso aceptable.</strong> No está permitido
              automatizar el acceso al servicio por encima de los límites de tu plan ni usar la
              API o el servidor MCP para fines distintos a los descritos aquí.
            </p>
          </section>

          <Separator />

          <section id="cookies" className="scroll-mt-20 space-y-4">
            <h2 className="text-lg font-semibold tracking-tight text-foreground">Cookies</h2>
            <p>
              Este servicio no usa cookies de terceros ni de analítica. Usa una única cookie propia
              y técnica, <code className="font-mono text-xs">radar_session</code>, estrictamente
              necesaria para mantener tu sesión iniciada (httpOnly: ni siquiera el propio código de
              la página puede leerla). Además, guarda tu preferencia de tema claro u oscuro (
              <code className="font-mono text-xs">theme</code>) en el almacenamiento local de tu
              navegador (<code>localStorage</code>). Ninguna de las dos se comparte con terceros.
              Al ser estrictamente necesarias para el funcionamiento del servicio, no verás un
              banner de cookies: no hay nada que consentir.
            </p>
          </section>

          <p className="pt-4 text-xs">
            <a href="/" className="text-primary underline-offset-4 hover:underline">
              ← Volver a la portada
            </a>
          </p>
        </main>
      </Container>
    </div>
  );
}
