# Multimedia University Smart Parking System

An automated, web-based parking management system developed for **Multimedia University of Kenya (Data Structures & Algorithms - Task One)**[cite: 1]. 

The system displays live parking slot availability before entry, records arriving vehicles, automatically calculates total duration and tiered parking fees on exit, and simulates barrier gate control upon payment confirmation[cite: 1, 2].

---

## Key Features & Client Requirements

- **Live Zone Floor Map:** Real-time visual display showing open slots (Emerald Green) vs taken spaces (Crimson Red) across Zone A, Zone B, and Zone C[cite: 1, 2].
- **Automated Slot Assignment:** Assigns the lowest-numbered available parking bay in $O(\log n)$ time using a Min-Heap[cite: 6].
- **Dynamic Tiered Pricing:** Configurable rates stored in SQLite (`rate_slabs` table) without needing code modifications[cite: 1, 2]:
  - Up to 30 mins: Free (Kshs 0)[cite: 1]
  - Up to 2 hours: Kshs 50[cite: 1]
  - Up to 4 hours: Kshs 100[cite: 1]
  - Up to 6 hours: Kshs 300[cite: 1]
  - Over 6 hours: Kshs 500[cite: 1]
- **M-Pesa Payment Simulation:** Collects payment and triggers physical barrier opening upon confirmation[cite: 1, 2].
- **Auditable Reconciliation:** Logs transaction amounts, methods, and timestamps for VAT and financial reconciliation[cite: 2].

---

## Tech Stack & Data Structures Used

| Component | Technology / Data Structure | Why It Was Chosen |
|---|---|---|
| **Backend** | Python 3, Flask | Lightweight framework ideal for web-based algorithmic demonstrations[cite: 1]. |
| **Database** | SQLite3 | Embedded relational database providing durability, foreign key integrity, and audit logging[cite: 6]. |
| **Slot Allocation** | Min-Heap (`heapq`) | Guarantees deterministic assignment of the lowest free slot number in $O(\log n)$ time[cite: 6]. |
| **Vehicle Lookup** | Hash Map (`dict`) | Provides instant $O(1)$ lookup for active parked vehicles using license plate numbers as keys[cite: 6]. |

---

## Project Structure

```text
mmu_parking_system/
│
├── schema.sql           # Database schema (slots, sessions, dynamic rates, payments)
├── parking_system.py    # Core parking engine (heapq, hashmap, fee tiers, DB queries)
├── app.py               # Flask web server, API routes, and interactive UI
├── README.md            # System documentation and instructions
└── parking_lot.db       # SQLite database file (generated automatically)
