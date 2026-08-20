import { useCallback, useMemo, useState } from "react";
import { calendar as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { CalendarEvent } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EVENT_TYPES = [
  { value: "article", label: "Article", color: "#3b82f6" },
  { value: "review", label: "Review", color: "#f59e0b" },
  { value: "publish", label: "Publish", color: "#22c55e" },
  { value: "meeting", label: "Meeting", color: "#8b5cf6" },
  { value: "deadline", label: "Deadline", color: "#ef4444" },
];

const STATUSES = ["planned", "in_progress", "review", "published", "overdue", "cancelled"];

const STATUS_COLORS: Record<string, string> = {
  planned: "gray",
  in_progress: "blue",
  review: "amber",
  published: "green",
  overdue: "red",
  cancelled: "gray",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "#9ca3af",
  normal: "#3b82f6",
  high: "#f59e0b",
  urgent: "#ef4444",
};

const TYPE_COLORS: Record<string, string> = {
  article: "#3b82f6",
  review: "#f59e0b",
  publish: "#22c55e",
  meeting: "#8b5cf6",
  deadline: "#ef4444",
};

// ---------------------------------------------------------------------------
// Calendar Grid
// ---------------------------------------------------------------------------

function CalendarGrid({ events, onEventClick }: { events: CalendarEvent[]; onEventClick: (e: CalendarEvent) => void }) {
  const [monthOffset, setMonthOffset] = useState(0);

  const today = new Date();
  const currentMonth = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Group events by date
  const eventsByDate: Record<string, CalendarEvent[]> = {};
  for (const e of events) {
    const dateKey = e.start_date;
    if (!eventsByDate[dateKey]) eventsByDate[dateKey] = [];
    eventsByDate[dateKey].push(e);
  }

  const monthName = currentMonth.toLocaleString("default", { month: "long", year: "numeric" });

  // Build calendar days
  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let d = 1; d <= daysInMonth; d++) days.push(d);

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <button className="small" onClick={() => setMonthOffset(monthOffset - 1)}>← Prev</button>
        <h3 style={{ margin: 0 }}>{monthName}</h3>
        <button className="small" onClick={() => setMonthOffset(monthOffset + 1)}>Next →</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 2 }}>
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
          <div key={d} style={{ textAlign: "center", fontSize: 11, fontWeight: 600, color: "#6b7280", padding: 4 }}>{d}</div>
        ))}
        {days.map((day, i) => {
          if (day === null) return <div key={`empty-${i}`} />;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const dayEvents = eventsByDate[dateStr] ?? [];
          const isToday = dateStr === today.toISOString().split("T")[0];

          return (
            <div key={i} style={{
              minHeight: 60,
              padding: 4,
              borderRadius: 4,
              border: isToday ? "2px solid #3b82f6" : "1px solid #e5e7eb",
              background: isToday ? "#eff6ff" : "white",
            }}>
              <div style={{ fontSize: 11, fontWeight: isToday ? 700 : 400, marginBottom: 2 }}>{day}</div>
              {dayEvents.slice(0, 3).map((e) => (
                <div
                  key={e.id}
                  onClick={() => onEventClick(e)}
                  style={{
                    fontSize: 10,
                    padding: "1px 4px",
                    borderRadius: 3,
                    background: TYPE_COLORS[e.event_type] ?? "#6b7280",
                    color: "white",
                    marginBottom: 1,
                    cursor: "pointer",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {e.title}
                </div>
              ))}
              {dayEvents.length > 3 && <div style={{ fontSize: 9, color: "#6b7280" }}>+{dayEvents.length - 3} more</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pipeline View
// ---------------------------------------------------------------------------

function PipelineView({ events, onEventClick }: { events: CalendarEvent[]; onEventClick: (e: CalendarEvent) => void }) {
  const grouped = useMemo(() => {
    const g: Record<string, CalendarEvent[]> = {};
    for (const s of STATUSES) g[s] = [];
    for (const e of events) {
      const key = STATUSES.includes(e.status) ? e.status : "planned";
      g[key].push(e);
    }
    return g;
  }, [events]);

  return (
    <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 8 }}>
      {STATUSES.map((status) => (
        <div key={status} style={{ minWidth: 200, flex: 1 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#374151", marginBottom: 8, display: "flex", alignItems: "center", gap: 4 }}>
            <Badge value={status} /> <span>{grouped[status].length}</span>
          </div>
          {grouped[status].map((e) => (
            <div
              key={e.id}
              onClick={() => onEventClick(e)}
              style={{
                padding: 8,
                marginBottom: 6,
                borderRadius: 6,
                border: "1px solid #e5e7eb",
                background: "white",
                cursor: "pointer",
                borderLeft: `3px solid ${TYPE_COLORS[e.event_type] ?? "#6b7280"}`,
              }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{e.title}</div>
              <div style={{ fontSize: 10, color: "#6b7280" }}>
                {e.start_date} · <Badge value={e.event_type} />
                {e.priority !== "normal" && <> · <span style={{ color: PRIORITY_COLORS[e.priority] }}>{e.priority}</span></>}
              </div>
              {e.assignee && <div style={{ fontSize: 10, color: "#9ca3af" }}>👤 {e.assignee}</div>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Event Form
// ---------------------------------------------------------------------------

function EventForm({ initial, onSave, onCancel }: { initial?: CalendarEvent; onSave: (data: Record<string, unknown>) => void; onCancel: () => void }) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [eventType, setEventType] = useState(initial?.event_type ?? "article");
  const [status, setStatus] = useState(initial?.status ?? "planned");
  const [startDate, setStartDate] = useState(initial?.start_date ?? new Date().toISOString().split("T")[0]);
  const [endDate, setEndDate] = useState(initial?.end_date ?? "");
  const [priority, setPriority] = useState(initial?.priority ?? "normal");
  const [assignee, setAssignee] = useState(initial?.assignee ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h4>{initial ? "Edit Event" : "New Event"}</h4>
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: 250 }} />
        <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
          {EVENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        {initial && (
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </select>
        )}
      </div>
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <label style={{ fontSize: 12 }}>Start: <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></label>
        <label style={{ fontSize: 12 }}>End: <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></label>
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          {["low", "normal", "high", "urgent"].map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <input placeholder="Assignee" value={assignee} onChange={(e) => setAssignee(e.target.value)} style={{ width: 150 }} />
      </div>
      <textarea placeholder="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} style={{ width: "100%", marginBottom: 8 }} />
      <div className="row" style={{ gap: 8 }}>
        <button className="small" onClick={() => onSave({ title, event_type: eventType, status, start_date: startDate, end_date: endDate || null, priority, assignee: assignee || null, notes: notes || null })} disabled={!title.trim()}>
          {initial ? "Update" : "Create"}
        </button>
        <button className="small secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type ViewMode = "calendar" | "pipeline";

export default function ContentCalendar() {
  const { active } = useWebsiteStore();
  const [viewMode, setViewMode] = useState<ViewMode>("calendar");
  const [showForm, setShowForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);

  // Fetch events for current month range
  const today = new Date();
  const startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1).toISOString().split("T")[0];
  const endDate = new Date(today.getFullYear(), today.getMonth() + 2, 0).toISOString().split("T")[0];

  const events = useAsync(
    () => active ? api.list(active.id, startDate, endDate, filterStatus) : Promise.resolve([]),
    [active?.id, filterStatus, startDate, endDate],
  );

  const save = useCallback(async (data: Record<string, unknown>) => {
    if (!active) return;
    try {
      if (editingEvent) {
        await api.update(editingEvent.id, data as Partial<CalendarEvent>);
      } else {
        await api.create({ ...data, website_id: active.id } as Parameters<typeof api.create>[0]);
      }
      setShowForm(false);
      setEditingEvent(null);
      await events.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, editingEvent, events]);

  const remove = useCallback(async (id: number) => {
    try {
      await api.delete(id);
      setShowForm(false);
      setEditingEvent(null);
      await events.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [events]);

  const handleEventClick = useCallback((e: CalendarEvent) => {
    setEditingEvent(e);
    setShowForm(true);
  }, []);

  if (!active) return <p className="muted">Select a website to view the calendar.</p>;
  if (events.loading) return <Loading />;

  const eventList: CalendarEvent[] = events.data ?? [];

  return (
    <>
      <h2 className="page-title">📅 Content Calendar</h2>
      <p className="page-sub">Schedule content, track deadlines, and manage the publishing pipeline.</p>

      {error && <ErrorBox message={error} />}

      {/* Controls */}
      <div className="row" style={{ gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {(["calendar", "pipeline"] as ViewMode[]).map((vm) => (
          <button key={vm} className={`small${viewMode === vm ? "" : " secondary"}`} onClick={() => setViewMode(vm)} style={{ fontWeight: viewMode === vm ? 700 : 400 }}>
            {vm === "calendar" ? "📅 Calendar" : "📋 Pipeline"}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <select value={filterStatus ?? ""} onChange={(e) => setFilterStatus(e.target.value || undefined)} style={{ fontSize: 12 }}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
        <button className="small" onClick={() => { setShowForm(!showForm); setEditingEvent(null); }}>
          {showForm ? "Cancel" : "+ New Event"}
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <EventForm
          initial={editingEvent ?? undefined}
          onSave={save}
          onCancel={() => { setShowForm(false); setEditingEvent(null); }}
        />
      )}

      {/* Event detail card when editing */}
      {editingEvent && showForm && (
        <div className="row" style={{ gap: 8, marginBottom: 16 }}>
          <button className="small" onClick={() => remove(editingEvent.id)} style={{ color: "#ef4444" }}>Delete Event</button>
        </div>
      )}

      {/* View */}
      {viewMode === "calendar" ? (
        <CalendarGrid events={eventList} onEventClick={handleEventClick} />
      ) : (
        <PipelineView events={eventList} onEventClick={handleEventClick} />
      )}
    </>
  );
}
