"""
Modern Parking Management System
---------------------------------
Implements: availability check, vehicle entry, vehicle exit with
duration/fee calculation, and slot release -- backed by SQLite.
"""

import heapq
import math
import sqlite3
import time
import os
from dataclasses import dataclass
from typing import Dict, List

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


@dataclass
class VehicleType:
    id: int
    name: str
    hourly_rate: float


@dataclass
class ActiveSession:
    """A vehicle currently parked. Kept in memory for O(1) access on exit."""
    plate: str
    vehicle_type_id: int
    slot_id: int
    entry_time: float
    session_id: int


class ParkingLot:
    def __init__(self, total_slots: int, vehicle_types: List[VehicleType],
                 db_path: str = ":memory:"):
        self.total_slots = total_slots
        self.vehicle_types: Dict[int, VehicleType] = {vt.id: vt for vt in vehicle_types}

        self.available_slots: List[int] = list(range(1, total_slots + 1))
        heapq.heapify(self.available_slots)

        self.active_sessions: Dict[str, ActiveSession] = {}

        self.db = sqlite3.connect(db_path)
        self._init_db(vehicle_types)

    def _init_db(self, vehicle_types: List[VehicleType]) -> None:
        with open(SCHEMA_PATH) as f:
            self.db.executescript(f.read())

        for vt in vehicle_types:
            self.db.execute(
                "INSERT OR IGNORE INTO vehicle_types (id, name, hourly_rate) VALUES (?, ?, ?)",
                (vt.id, vt.name, vt.hourly_rate),
            )
        for slot_id in range(1, self.total_slots + 1):
            self.db.execute(
                "INSERT OR IGNORE INTO parking_slots (slot_id, status) VALUES (?, 'FREE')",
                (slot_id,),
            )
        self.db.commit()

    def check_availability(self) -> dict:
        return {
            "total_slots": self.total_slots,
            "available_slots": len(self.available_slots),
            "occupied_slots": self.total_slots - len(self.available_slots),
        }

    def vehicle_entry(self, plate: str, vehicle_type_id: int) -> int:
        if plate in self.active_sessions:
            raise ValueError(f"Vehicle {plate} is already parked.")
        if not self.available_slots:
            raise RuntimeError("Parking lot is full.")
        if vehicle_type_id not in self.vehicle_types:
            raise ValueError(f"Unknown vehicle_type_id {vehicle_type_id}")

        slot_id = heapq.heappop(self.available_slots)
        entry_time = time.time()

        cur = self.db.execute(
            "INSERT INTO parking_sessions "
            "(plate_number, vehicle_type_id, slot_id, entry_time, status) "
            "VALUES (?, ?, ?, ?, 'ACTIVE')",
            (plate, vehicle_type_id, slot_id, entry_time),
        )
        self.db.execute(
            "UPDATE parking_slots SET status = 'OCCUPIED' WHERE slot_id = ?",
            (slot_id,),
        )
        self.db.commit()

        self.active_sessions[plate] = ActiveSession(
            plate=plate,
            vehicle_type_id=vehicle_type_id,
            slot_id=slot_id,
            entry_time=entry_time,
            session_id=cur.lastrowid,
        )
        return slot_id

    def vehicle_exit(self, plate: str) -> dict:
        session = self.active_sessions.get(plate)
        if session is None:
            raise ValueError(f"Vehicle {plate} was not found in the lot.")

        exit_time = time.time()
        duration_hours = max((exit_time - session.entry_time) / 3600, 0)
        fee = self._calculate_fee(duration_hours, session.vehicle_type_id)

        self.db.execute(
            "UPDATE parking_sessions SET exit_time = ?, fee = ?, status = 'CLOSED'"
            " WHERE id = ?",
            (exit_time, fee, session.session_id),
        )
        self.db.execute(
            "UPDATE parking_slots SET status = 'FREE' WHERE slot_id = ?",
            (session.slot_id,),
        )
        self.db.commit()

        heapq.heappush(self.available_slots, session.slot_id)
        del self.active_sessions[plate]

        return {
            "plate": plate,
            "slot_id": session.slot_id,
            "duration_hours": round(duration_hours, 2),
            "fee": fee,
        }

    def _calculate_fee(self, duration_hours: float, vehicle_type_id: int) -> float:
        rate = self.vehicle_types[vehicle_type_id].hourly_rate
        billable_hours = max(1, math.ceil(duration_hours))
        return round(billable_hours * rate, 2)

    def close(self):
        self.db.close()

