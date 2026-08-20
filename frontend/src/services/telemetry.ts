/** Local usage analytics + browser crash reporting.
 *
 * Privacy posture: events go only to the local backend (usage_events table).
 * Nothing leaves the machine unless the user configured Sentry themselves.
 */
import { diagnostics } from "./backend";

export type TrackEvent = "page_view" | "action";

/** Fire-and-forget — analytics must never throw into the UI. */
export function track(event: TrackEvent, detail?: string): void {
  diagnostics.track(event, detail).catch(() => undefined);
}

/** Global error handlers → POST /diagnostics/crash (logged + optionally Sentry). */
export function installCrashReporter(getRoute: () => string): void {
  window.addEventListener("error", (event) => {
    const message = event.message || "Unknown error";
    const stack = event.error instanceof Error ? event.error.stack : undefined;
    diagnostics.crash(message, stack, getRoute()).catch(() => undefined);
  });

  window.addEventListener("unhandledrejection", (event) => {
    const reason: unknown = event.reason;
    const message = reason instanceof Error ? reason.message : String(reason);
    const stack = reason instanceof Error ? reason.stack : undefined;
    diagnostics.crash(`Unhandled rejection: ${message}`, stack, getRoute()).catch(() => undefined);
  });
}
