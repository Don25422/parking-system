"""
Modern Parking Management System
"""

import heapq
import math
import sqlite3
import time
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

@dataclass
class ActiveSession:
    plate: str
    vehicle_type_id: int
    slot_id: int
    entry_time: float
    session_id: int


class ParkingLot:
    def __init__(self, total_slots: int = 10, db_path: str = "parking_lot.db"):
        self.total_slots = total_slots
        self.db_path = db_path
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        
        self.available_slots: List[int] = list(range(1, total_slots + 1))
        heapq.heapify(self.available_slots)
        self.active_sessions: Dict[str, ActiveSession] = {}
        
        self._init_db()
        self._sync_state_from_db()

    def _init_db(self) -> None:
        with open(SCHEMA_PATH) as f:
            self.db.executescript(f.read())

        # Populate dynamic fee tiers if empty
        cur = self.db.execute("SELECT COUNT(*) FROM rate_slabs")
        if cur.fetchone()[0] == 0:
            default_rates = [
                (30, 0.0),       # Up to 30 mins: Free
                (120, 50.0),     # Up to 2 hours: Kshs 50
                (240, 100.0),    # Up to 4 hours: Kshs 100
                (360, 300.0),    # Up to 6 hours: Kshs 300
                (999999, 500.0)  # Over 6 hours: Kshs 500
            ]
            self.db.executemany(
                "INSERT INTO rate_slabs (max_minutes, fee_ksh) VALUES (?, ?)", default_rates
            )

        for slot_id in range(1, self.total_slots + 1):
            self.db.execute(
                "INSERT OR IGNORE INTO parking_slots (slot_id, status) VALUES (?, 'FREE')",
                (slot_id,),
            )
        self.db.commit()

    def _sync_state_from_db(self) -> None:
        """Rebuilds in-memory heap and active sessions from DB on startup."""
        occupied = set()
        cur = self.db.execute(
            "SELECT id, plate_number, vehicle_type_id, slot_id, entry_time "
            "FROM parking_sessions WHERE status = 'ACTIVE'"
        )
        for row in cur.fetchall():
            self.active_sessions[row["plate_number"]] = ActiveSession(
                plate=row["plate_number"],
                vehicle_type_id=row["vehicle_type_id"],
                slot_id=row["slot_id"],
                entry_time=row["entry_time"],
                session_id=row["id"]
            )
            occupied.add(row["slot_id"])

        self.available_slots = [s for s in range(1, self.total_slots + 1) if s not in occupied]
        heapq.heapify(self.available_slots)

    def check_availability(self) -> dict:
        return {
            "total_slots": self.total_slots,
            "available_slots": len(self.available_slots),
            "occupied_slots": self.total_slots - len(self.available_slots),
            "free_slots_list": sorted(self.available_slots)
        }

    def vehicle_entry(self, plate: str, vehicle_type_id: int = 1) -> dict:
        plate = plate.upper().strip()
        if plate in self.active_sessions:
            raise ValueError(f"Vehicle {plate} is already inside.")
        if not self.available_slots:
            raise RuntimeError("Parking Lot is full!")

        slot_id = heapq.heappop(self.available_slots)
        entry_time = time.time()

        cur = self.db.execute(
            "INSERT INTO parking_sessions (plate_number, vehicle_type_id, slot_id, entry_time, status) "
            "VALUES (?, ?, ?, ?, 'ACTIVE')",
            (plate, vehicle_type_id, slot_id, entry_time)
        )
        self.db.execute("UPDATE parking_slots SET status = 'OCCUPIED' WHERE slot_id = ?", (slot_id,))
        self.db.commit()

        self.active_sessions[plate] = ActiveSession(
            plate=plate,
            vehicle_type_id=vehicle_type_id,
            slot_id=slot_id,
            entry_time=entry_time,
            session_id=cur.lastrowid
        )
        return {"plate": plate, "slot_id": slot_id, "entry_time": entry_time}

    def calculate_fee_for_plate(self, plate: str) -> dict:
        session = self.active_sessions.get(plate.upper().strip())
        if not session:
            raise ValueError(f"Vehicle {plate} not found in lot.")

        exit_time = time.time()
        duration_minutes = max((exit_time - session.entry_time) / 60, 0)
        
        # Determine fee tier from dynamic database table
        cur = self.db.execute(
            "SELECT fee_ksh FROM rate_slabs WHERE max_minutes >= ? ORDER BY max_minutes ASC LIMIT 1",
            (duration_minutes,)
        )
        row = cur.fetchone()
        fee = row["fee_ksh"] if row else 500.0

        return {
            "session_id": session.session_id,
            "plate": plate,
            "slot_id": session.slot_id,
            "duration_minutes": round(duration_minutes, 2),
            "fee_ksh": fee
        }

    def vehicle_exit_and_pay(self, plate: str, payment_method: str = "M-Pesa") -> dict:
        fee_info = self.calculate_fee_for_plate(plate)
        session = self.active_sessions[plate.upper().strip()]
        exit_time = time.time()

        # Record payment transaction (Auditable record)
        self.db.execute(
            "INSERT INTO payments (session_id, amount, payment_method, timestamp) VALUES (?, ?, ?, ?)",
            (session.session_id, fee_info["fee_ksh"], payment_method, exit_time)
        )

        # Close session
        self.db.execute(
            "UPDATE parking_sessions SET exit_time = ?, fee = ?, status = 'CLOSED' WHERE id = ?",
            (exit_time, fee_info["fee_ksh"], session.session_id)
        )
        self.db.execute("UPDATE parking_slots SET status = 'FREE' WHERE slot_id = ?", (session.slot_id,))
        self.db.commit()

        # Free memory structures
        heapq.heappush(self.available_slots, session.slot_id)
        del self.active_sessions[plate.upper().strip()]

        return {
            "status": "SUCCESS",
            "barrier_opened": True,
            "plate": plate,
            "fee_paid": fee_info["fee_ksh"],
            "payment_method": payment_method
        }

    def close(self):
        self.db.close()

