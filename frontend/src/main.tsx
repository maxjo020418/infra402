import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

console.log("main.tsx loaded (DEV)", import.meta.env.MODE, import.meta.env);
const root = document.getElementById("root");
if (root) root.textContent = "DEV BOOT TEST";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
