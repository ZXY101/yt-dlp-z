import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import { App } from "@/app/app";
import { initTheme } from "@/lib/theme";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element");
}

initTheme();
createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
