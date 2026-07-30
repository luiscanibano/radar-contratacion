import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/index.css";
import { Legal } from "@/pages/Legal";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Legal />
  </StrictMode>,
);
