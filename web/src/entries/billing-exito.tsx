import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/index.css";
import { BillingResult } from "@/pages/BillingResult";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BillingResult variante="exito" />
  </StrictMode>,
);
