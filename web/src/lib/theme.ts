const STORAGE_KEY = "theme";

export type Theme = "light" | "dark";

// El script que resuelve el tema antes del primer paint (evita el flash de
// tema incorrecto) vive en public/theme-init.js, cargado como <script src>
// en cada HTML de entrada — no aquí. Mantener STORAGE_KEY en sync con ese
// archivo si cambia.

export function getTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function setTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
  localStorage.setItem(STORAGE_KEY, theme);
}

export function toggleTheme(): Theme {
  const next: Theme = getTheme() === "dark" ? "light" : "dark";
  setTheme(next);
  return next;
}
