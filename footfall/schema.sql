-- Footfall shared data contract (MVP). Unknown values are NULL, never invented defaults.
-- All timestamps are ISO 8601 strings with an explicit UTC offset.

CREATE TABLE IF NOT EXISTS businesses (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'Europe/Dublin',
  opens TEXT NOT NULL,              -- 'HH:MM'
  closes TEXT NOT NULL,             -- 'HH:MM'
  open_days TEXT NOT NULL,          -- JSON list, e.g. ["mon","tue",...]
  radius_m INTEGER NOT NULL,
  sales_baseline TEXT,              -- optional JSON, owner-supplied
  avg_spend REAL,                   -- optional, owner-supplied
  demo_label TEXT
);

CREATE TABLE IF NOT EXISTS supplier_constraints (
  id TEXT PRIMARY KEY,
  business_id TEXT NOT NULL REFERENCES businesses(id),
  supplier TEXT NOT NULL,
  contact_label TEXT,
  delivery_day TEXT NOT NULL,       -- 'mon'..'sun'
  delivery_window TEXT,             -- 'HH:MM-HH:MM'
  cutoff_rule TEXT NOT NULL,        -- JSON, see domain/cutoffs.py
  evidence TEXT,                    -- original message text, or NULL
  demo_label TEXT                   -- set when the rule is a demo assumption
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  org_name TEXT NOT NULL,
  venue_name TEXT,
  url TEXT NOT NULL,
  type TEXT NOT NULL,               -- university|venue|community|church|hotel|listing|council
  lat REAL,
  lon REAL,
  access_notes TEXT,
  refresh_interval_h INTEGER NOT NULL DEFAULT 24,
  last_attempt_at TEXT,
  last_success_at TEXT,
  status TEXT NOT NULL DEFAULT 'never_checked',  -- never_checked|ok|error
  last_error TEXT,
  provenance TEXT                   -- how/when Olan found this source
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  norm_key TEXT NOT NULL UNIQUE,    -- normalised title|local date|venue
  start_at TEXT,
  end_at TEXT,
  time_precision TEXT NOT NULL DEFAULT 'datetime',  -- datetime|date|unknown
  venue_name TEXT,
  lat REAL,
  lon REAL,
  category TEXT,
  access TEXT NOT NULL DEFAULT 'unknown',           -- public|restricted|unknown
  status TEXT NOT NULL DEFAULT 'listed',            -- listed|unknown (never inferred 'cancelled')
  verification TEXT NOT NULL DEFAULT 'unverified',  -- verified|unverified|prepared
  attendance INTEGER,
  possible_duplicate_of TEXT,
  data_mode TEXT NOT NULL DEFAULT 'live',           -- live|prepared
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL REFERENCES events(id),
  source_id TEXT REFERENCES sources(id),
  url TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  excerpt TEXT,
  extracted_json TEXT,
  uncertainty TEXT,
  UNIQUE(event_id, url, excerpt)
);

CREATE TABLE IF NOT EXISTS weather (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  day TEXT NOT NULL,                -- local date the summary applies to
  temp_max REAL,
  rain_prob_max INTEGER,
  wind_max REAL,
  units TEXT NOT NULL,              -- JSON
  provider TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'forecast',  -- forecast|observation
  UNIQUE(lat, lon, day, kind)
);

CREATE TABLE IF NOT EXISTS drafts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  insight_id TEXT NOT NULL,
  recipient_label TEXT NOT NULL,
  text TEXT NOT NULL,
  source TEXT NOT NULL,             -- template|llm
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  approved_at TEXT                  -- approval only; there is no delivered state
);

CREATE TABLE IF NOT EXISTS refresh_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  mode TEXT NOT NULL,               -- live|prepared
  status TEXT NOT NULL,             -- running|ok|partial|failed
  sources_attempted INTEGER NOT NULL DEFAULT 0,
  sources_succeeded INTEGER NOT NULL DEFAULT 0,
  events_upserted INTEGER NOT NULL DEFAULT 0,
  llm_calls INTEGER NOT NULL DEFAULT 0,
  errors TEXT NOT NULL DEFAULT '[]' -- JSON list
);
