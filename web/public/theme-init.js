// Inline antes (duplicado en cada HTML de entrada) para evitar el flash de
// tema incorrecto (FOUC) antes de que React monte. Ahora vive en un archivo
// externo — cargado como <script src> en vez de <script> inline — para que
// la CSP (script-src 'self', ver api/main.py) no necesite 'unsafe-inline'.
// Mantener en sync con src/lib/theme.ts (mismo STORAGE_KEY: "theme").
(function () {
  try {
    var s = localStorage.getItem("theme");
    var d = s ? s === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", d);
  } catch (e) {}
})();
