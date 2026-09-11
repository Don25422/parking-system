CREATE TABLE IF NOT EXISTS vehicle_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    hourly_rate REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY,
    floor INTEGER DEFAULT 1,
    vehicle_type_id INTEGER,
    status TEXT NOT NULL DEFAULT 'FREE' CHECK (status IN ('FREE', 'OCCUPIED')),
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(id)
);

CREATE TABLE IF NOT EXISTS parking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL,
    vehicle_type_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    entry_time REAL NOT NULL,
    exit_time REAL,
    fee REAL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED')),
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(id),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);

CREATE INDEX IF NOT EXISTS idx_active_plate
ON parking_sessions (plate_number)
WHERE status = 'ACTIVE';