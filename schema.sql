CREATE TABLE IF NOT EXISTS vehicle_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS rate_slabs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    max_minutes INTEGER NOT NULL,
    fee_ksh REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY,
    floor INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'FREE' CHECK (status IN ('FREE', 'OCCUPIED'))
);

CREATE TABLE IF NOT EXISTS parking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL,
    vehicle_type_id INTEGER DEFAULT 1,
    slot_id INTEGER NOT NULL,
    entry_time REAL NOT NULL,
    exit_time REAL,
    fee REAL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED')),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    timestamp REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES parking_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_active_plate
ON parking_sessions (plate_number)
WHERE status = 'ACTIVE';