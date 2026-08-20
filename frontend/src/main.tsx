import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./app/App";
import { bootstrapBackendToken } from "./services/desktop";
import { installCrashReporter } from "./services/telemetry";
import "./styles.css";

// Crash reporting must be active before anything else renders.
installCrashReporter(() => window.location.pathname);

// Fetch the per-launch backend token from the Tauri shell (desktop only)
// before the first render so initial API calls carry X-Backend-Token.
void bootstrapBackendToken().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>,
  );
});
