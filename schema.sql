-- Schema for the Incident Log Analyzer database

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Table to store road rules
CREATE TABLE IF NOT EXISTS ruleset (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    max_speed REAL NOT NULL,
    min_follow_distance REAL NOT NULL,
    stop_sign_wait REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(max_speed, min_follow_distance, stop_sign_wait)
);

-- Table to store scenarios
CREATE TABLE IF NOT EXISTS scenario (
    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    source_file TEXT NOT NULL,
    rule_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES ruleset(rule_id)
);

-- Table to store speed zones for scenarios
CREATE TABLE IF NOT EXISTS speed_zone (
    zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    start_mile REAL NOT NULL,
    end_mile REAL NOT NULL,
    speed_limit REAL NOT NULL,
    FOREIGN KEY (scenario_id) REFERENCES scenario(scenario_id) ON DELETE CASCADE,
    CHECK (start_mile < end_mile)
);

-- Table to store violations
CREATE TABLE IF NOT EXISTS violation (
    violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    tstamp TEXT NOT NULL,  -- Formatted time string (MM:SS.s)
    type TEXT NOT NULL,    -- Violation type (SPEEDING, TAILGATING, etc.)
    details TEXT NOT NULL, -- Details about the violation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenario(scenario_id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_violation_scenario ON violation(scenario_id);
CREATE INDEX IF NOT EXISTS idx_violation_type ON violation(type);
CREATE INDEX IF NOT EXISTS idx_violation_time ON violation(tstamp);
