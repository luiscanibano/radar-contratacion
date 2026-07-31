/** Nombre del evento global disparado cuando una petición vuelve con un 401
 * inesperado (sesión caducada o cookie borrada): permite a AppPanel volver a
 * la pantalla de login sin que cada componente que llama a la API tenga que
 * gestionarlo por su cuenta. */
export const EVENTO_SESION_CADUCADA = "radar:sesion-caducada";

export class SesionCaducadaError extends Error {}

/** Fetch wrapper: la sesión viaja en una cookie httpOnly (el navegador la
 * adjunta solo — no hay ningún token que leer ni inyectar aquí, así un XSS
 * no puede robarla de localStorage). `gestionar401` se desactiva en
 * login/registro, donde un 401 es "credenciales incorrectas", no "sesión
 * caducada". */
async function llamar(
  ruta: string,
  opciones: RequestInit = {},
  { gestionar401 = true }: { gestionar401?: boolean } = {},
): Promise<Response> {
  const cabeceras = new Headers(opciones.headers);
  cabeceras.set("Content-Type", "application/json");

  const respuesta = await fetch(ruta, { ...opciones, headers: cabeceras });
  if (respuesta.status === 401 && gestionar401) {
    window.dispatchEvent(new CustomEvent(EVENTO_SESION_CADUCADA));
    throw new SesionCaducadaError("Tu sesión ha caducado. Vuelve a iniciar sesión.");
  }
  return respuesta;
}

async function detalleError(respuesta: Response, porDefecto: string): Promise<string> {
  try {
    const cuerpo = await respuesta.json();
    return cuerpo.detail || porDefecto;
  } catch {
    return porDefecto;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface Credenciales {
  email: string;
  password: string;
}

export interface CredencialesRegistro extends Credenciales {
  acepta_terminos: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Usuario {
  email: string;
}

export interface Alerta {
  id: number;
  consulta_texto: string;
}

export interface ResultadoBusqueda {
  entry_id: string;
  expediente: string | null;
  objeto: string | null;
  organo: string | null;
  cpv_division: string | null;
  anio: number | null;
  presupuesto: number | null;
  score: number;
}

export interface InfoPlan {
  plan: string;
  cuota: number | null;
  usadas: number;
  restantes: number | null;
}

export async function login(credenciales: Credenciales): Promise<void> {
  const respuesta = await llamar(
    "/auth/login",
    { method: "POST", body: JSON.stringify(credenciales) },
    { gestionar401: false },
  );
  if (respuesta.status === 403) {
    throw new ApiError(403, await detalleError(respuesta, "Confirma tu email antes de iniciar sesión."));
  }
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo iniciar sesión."));
  }
}

/** El registro ya no abre sesión: la cuenta queda pendiente de confirmar por
 * email (ver /auth/verificar) y el backend devuelve solo un mensaje. */
export async function registrar(credenciales: CredencialesRegistro): Promise<string> {
  const respuesta = await llamar(
    "/auth/registro",
    { method: "POST", body: JSON.stringify(credenciales) },
    { gestionar401: false },
  );
  if (respuesta.status === 409) {
    throw new ApiError(409, "Ese email ya está registrado. Inicia sesión.");
  }
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo crear la cuenta."));
  }
  const datos = await respuesta.json();
  return datos.mensaje;
}

export async function reenviarVerificacion(email: string): Promise<string> {
  const respuesta = await llamar(
    "/auth/reenviar-verificacion",
    { method: "POST", body: JSON.stringify({ email }) },
    { gestionar401: false },
  );
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo reenviar el email."));
  }
  const datos = await respuesta.json();
  return datos.mensaje;
}

export async function olvidePassword(email: string): Promise<string> {
  const respuesta = await llamar(
    "/auth/olvide-password",
    { method: "POST", body: JSON.stringify({ email }) },
    { gestionar401: false },
  );
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo procesar la solicitud."));
  }
  const datos = await respuesta.json();
  return datos.mensaje;
}

export async function resetearPassword(token: string, password: string): Promise<void> {
  const respuesta = await llamar(
    "/auth/resetear-password",
    { method: "POST", body: JSON.stringify({ token, password }) },
    { gestionar401: false },
  );
  if (!respuesta.ok) {
    throw new ApiError(
      respuesta.status,
      await detalleError(respuesta, "No se pudo restablecer la contraseña."),
    );
  }
}

export async function logout(): Promise<void> {
  await llamar("/auth/logout", { method: "POST" }, { gestionar401: false });
}

export async function quienSoy(): Promise<Usuario> {
  const respuesta = await llamar("/auth/me", {}, { gestionar401: false });
  if (!respuesta.ok) throw new ApiError(respuesta.status, "No se pudo verificar la sesión.");
  return respuesta.json();
}

/** Token nuevo para pegar en un cliente MCP externo (ver CuentaSeccion). Se
 * pide bajo demanda: a diferencia de la sesión, sí sale del navegador, así
 * que no se guarda en ningún sitio — solo vive en memoria hasta que el
 * usuario lo copia. */
export async function obtenerTokenMcp(): Promise<string> {
  const respuesta = await llamar("/auth/mcp-token", { method: "POST" });
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo generar el token."));
  }
  const datos: Token = await respuesta.json();
  return datos.access_token;
}

export async function preguntar(texto: string): Promise<string> {
  const respuesta = await llamar("/preguntar", {
    method: "POST",
    body: JSON.stringify({ texto }),
  });
  if (respuesta.status === 402) {
    throw new ApiError(402, "Has agotado la cuota mensual de tu plan. Amplíala más abajo.");
  }
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "El agente no pudo responder."));
  }
  const datos = await respuesta.json();
  return datos.respuesta;
}

export async function listarAlertas(): Promise<Alerta[]> {
  const respuesta = await llamar("/alertas");
  if (!respuesta.ok) throw new ApiError(respuesta.status, "No se pudieron cargar las alertas.");
  return respuesta.json();
}

export async function crearAlerta(consulta_texto: string): Promise<Alerta> {
  const respuesta = await llamar("/alertas", {
    method: "POST",
    body: JSON.stringify({ consulta_texto }),
  });
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo crear la alerta."));
  }
  return respuesta.json();
}

export async function borrarAlerta(id: number): Promise<void> {
  const respuesta = await llamar(`/alertas/${id}`, { method: "DELETE" });
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo borrar la alerta."));
  }
}

export async function crearCheckout(plan: string): Promise<string> {
  const respuesta = await llamar("/billing/checkout", {
    method: "POST",
    body: JSON.stringify({ plan }),
  });
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo iniciar el pago."));
  }
  const datos = await respuesta.json();
  return datos.checkout_url;
}

export async function abrirPortal(): Promise<string> {
  const respuesta = await llamar("/billing/portal", { method: "POST" });
  if (!respuesta.ok) {
    throw new ApiError(
      respuesta.status,
      await detalleError(respuesta, "No se pudo abrir la gestión de la suscripción."),
    );
  }
  const datos = await respuesta.json();
  return datos.portal_url;
}

export async function miPlan(): Promise<InfoPlan> {
  const respuesta = await llamar("/me/plan");
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo cargar tu plan."));
  }
  return respuesta.json();
}

export async function buscarLicitaciones(q: string, k = 10): Promise<ResultadoBusqueda[]> {
  const parametros = new URLSearchParams({ q, k: String(k) });
  const respuesta = await llamar(`/buscar?${parametros}`);
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await detalleError(respuesta, "No se pudo completar la búsqueda."));
  }
  const datos = await respuesta.json();
  return datos.resultados;
}
