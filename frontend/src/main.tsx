import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import { App } from "@/app/app";
import { applySystemTheme } from "@/lib/theme";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element");
}

applySystemTheme();
createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
