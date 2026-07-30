import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/index.css";
import { AppPanel } from "@/pages/AppPanel";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppPanel />
  </StrictMode>,
);
