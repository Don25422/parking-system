from flask import Flask, render_template_string, request, jsonify
from parking_system import ParkingLot
import datetime

app = Flask(__name__)
# 18 slots total: Zone A (Slots 1-6), Zone B (Slots 7-12), Zone C (Slots 13-18)
lot = ParkingLot(total_slots=18, db_path="parking_lot.db")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multimedia University Smart Parking System</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* User Specified Palette */
            --canvas-bg: #f1f5f9;            /* Neutral light-grey canvas */
            --surface: #ffffff;              /* Soft-white container */
            --border-light: #e2e8f0;
            --text-dark: #0f172a;
            --text-sub: #64748b;
            
            --slot-open: #10b981;            /* Emerald Green for open slots */
            --slot-taken: #ef4444;           /* Crimson Red for taken spaces */
            --slot-active: #2563eb;          /* Electric Blue for active selection */
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: var(--canvas-bg); color: var(--text-dark); min-height: 100vh; padding: 1.5rem; }

        .app-shell { max-width: 1300px; margin: 0 auto; background: var(--surface); border-radius: 24px; padding: 1.5rem; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }

        /* Top Bar & Branding */
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .brand-name { font-size: 1.35rem; font-weight: 700; color: var(--text-dark); }
        .nav-pills { display: flex; background: #e2e8f0; padding: 4px; border-radius: 30px; gap: 4px; }
        .pill-btn { border: none; padding: 0.5rem 1.25rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem; cursor: pointer; background: transparent; color: var(--text-sub); }
        .pill-btn.active { background: var(--slot-active); color: #fff; }

        /* Layout Grid */
        .dashboard-grid { display: grid; grid-template-columns: 2.2fr 1fr; gap: 1.5rem; }
        @media(max-width: 980px) { .dashboard-grid { grid-template-columns: 1fr; } }

        .card { background: var(--surface); border: 1px solid var(--border-light); border-radius: 20px; padding: 1.25rem; margin-bottom: 1.25rem; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .card-title { font-size: 1.1rem; font-weight: 700; color: var(--text-dark); }

        /* Dynamic Zone Filter Tabs */
        .zone-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
        .zone-tab { border: 1px solid var(--border-light); padding: 0.55rem 1.25rem; border-radius: 12px; font-weight: 600; font-size: 0.85rem; background: #f8fafc; color: var(--text-sub); cursor: pointer; transition: all 0.2s; }
        .zone-tab.active { background: var(--slot-active); color: #ffffff; border-color: var(--slot-active); }

        /* Floor Slot Grid */
        .slot-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; background: #f8fafc; padding: 1.25rem; border-radius: 16px; border: 1px solid var(--border-light); }
        .slot-cell { background: #ffffff; border: 2px dashed var(--slot-open); border-radius: 14px; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; cursor: pointer; transition: all 0.2s; }
        .slot-cell.open { background: rgba(16, 185, 129, 0.05); }
        .slot-cell.taken { border-style: solid; border-color: var(--slot-taken); background: rgba(239, 68, 68, 0.08); }
        .slot-cell.active-selected { border-style: solid; border-color: var(--slot-active); background: rgba(37, 99, 235, 0.1); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25); }
        
        .slot-number { position: absolute; top: 8px; left: 10px; font-size: 0.75rem; font-weight: 700; color: var(--text-sub); }
        
        /* Top-down Car Graphic */
        .car-icon { width: 32px; height: 58px; background: #1e293b; border-radius: 8px; position: relative; margin-top: 10px; border: 2px solid var(--slot-taken); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .car-icon::before { content: ''; position: absolute; top: 10px; left: 3px; right: 3px; height: 12px; background: #64748b; border-radius: 3px; }
        .car-icon::after { content: ''; position: absolute; bottom: 10px; left: 3px; right: 3px; height: 8px; background: #475569; border-radius: 2px; }
        .slot-plate { font-size: 0.72rem; font-weight: 700; color: var(--text-dark); margin-top: 4px; }

        /* Right Panel Cards */
        .stat-block { display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1rem; background: #f8fafc; border-radius: 14px; margin-bottom: 0.6rem; border: 1px solid var(--border-light); }
        .stat-val { font-size: 1.2rem; font-weight: 700; }

        /* Form Controls */
        .form-group { margin-bottom: 0.85rem; }
        label { display: block; font-size: 0.8rem; font-weight: 600; color: var(--text-sub); margin-bottom: 0.35rem; }
        input { width: 100%; border: 1px solid var(--border-light); padding: 0.7rem 1rem; border-radius: 12px; font-size: 0.9rem; outline: none; background: #f8fafc; }
        input:focus { border-color: var(--slot-active); background: #fff; }

        .btn { width: 100%; padding: 0.75rem; border-radius: 12px; border: none; font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: opacity 0.2s; }
        .btn-active { background: var(--slot-active); color: #fff; }
        .btn-emerald { background: var(--slot-open); color: #fff; }

        /* Active Directory Table */
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 0.5rem; }
        th { text-align: left; color: var(--text-sub); padding: 0.5rem; border-bottom: 1px solid var(--border-light); }
        td { padding: 0.65rem 0.5rem; border-bottom: 1px solid var(--border-light); }
    </style>
</head>
<body>

<div class="app-shell">
    <header>
        <div class="brand-name">Multimedia University Smart Parking System</div>
        <div class="nav-pills">
            <button class="pill-btn active">Dashboard</button>
            <button class="pill-btn" onclick="resetSystem()">Reset Database</button>
        </div>
    </header>

    <div class="dashboard-grid">
        <!-- Left Section: Floor Map & Active Vehicle Directory -->
        <div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Live Zone Floor Map</div>
                </div>

                <!-- Dynamic Zone Filter Tabs -->
                <div class="zone-tabs">
                    <button id="tab-A" class="zone-tab active" onclick="switchZone('A')">Zone A (Slots 1-6)</button>
                    <button id="tab-B" class="zone-tab" onclick="switchZone('B')">Zone B (Slots 7-12)</button>
                    <button id="tab-C" class="zone-tab" onclick="switchZone('C')">Zone C (Slots 13-18)</button>
                </div>

                <div id="slots-grid" class="slot-grid"></div>
            </div>

            <!-- Active Parked Vehicles Directory -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Active Parked Vehicles</div>
                    <span style="font-size:0.85rem; color:var(--text-sub);" id="active-count">0 Parked</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Plate</th>
                            <th>Zone Bay</th>
                            <th>Check-in Time</th>
                            <th>Tariff</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="active-table-body">
                        <tr><td colspan="5" style="text-align:center; color:var(--text-sub);">No active parked vehicles</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Right Section: Overview & Control Terminals -->
        <div>
            <div class="card">
                <div class="card-title" style="margin-bottom:1rem;">Parking Overview</div>
                <div class="stat-block">
                    <span style="font-weight:600; color:var(--text-sub);">Total Capacity</span>
                    <span class="stat-val" id="stat-total">-</span>
                </div>
                <div class="stat-block">
                    <span style="font-weight:600; color:var(--text-sub);">Open Slots</span>
                    <span class="stat-val" style="color:var(--slot-open);" id="stat-avail">-</span>
                </div>
                <div class="stat-block">
                    <span style="font-weight:600; color:var(--text-sub);">Taken Spaces</span>
                    <span class="stat-val" style="color:var(--slot-taken);" id="stat-occ">-</span>
                </div>
            </div>

            <!-- Vehicle Entry Card -->
            <div class="card">
                <div class="card-title" style="margin-bottom:1rem;">Vehicle Entry Terminal</div>
                <div class="form-group">
                    <label>License Plate Number</label>
                    <input type="text" id="entry-plate" placeholder="e.g. KDA 123B">
                </div>
                <button class="btn btn-active" onclick="recordEntry()">Record Arrival & Assign Slot</button>
            </div>

            <!-- Checkout & Payment Card -->
            <div class="card">
                <div class="card-title" style="margin-bottom:1rem;">Exit & Barrier Clearance</div>
                <div class="form-group">
                    <label>License Plate Number</label>
                    <input type="text" id="exit-plate" placeholder="e.g. KDA 123B">
                </div>
                <button class="btn btn-active" style="background:#475569;" onclick="calculateFee()">Calculate Fee</button>

                <div id="checkout-panel" style="display:none; margin-top:1rem; background:#f8fafc; padding:1rem; border-radius:14px; border:1px solid var(--border-light);">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem; font-size:0.85rem;">
                        <span>Duration</span>
                        <b id="bill-duration">-</b>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:1rem; font-size:1rem; font-weight:700;">
                        <span>Total Payable</span>
                        <span>Kshs. <span id="bill-amount">0</span></span>
                    </div>
                    <button class="btn btn-emerald" onclick="processPayment('M-Pesa')">Simulate M-Pesa & Open Barrier</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    let currentZone = 'A';
    let selectedSlotId = null;

    function switchZone(zone) {
        currentZone = zone;
        document.querySelectorAll('.zone-tab').forEach(tab => tab.classList.remove('active'));
        document.getElementById('tab-' + zone).classList.add('active');
        refreshDisplay();
    }

    function selectSlot(slotId, plate) {
        selectedSlotId = slotId;
        if(plate) {
            document.getElementById('exit-plate').value = plate;
            calculateFee();
        }
        refreshDisplay();
    }

    function getZoneRange(zone) {
        if (zone === 'A') return { start: 1, end: 6 };
        if (zone === 'B') return { start: 7, end: 12 };
        if (zone === 'C') return { start: 13, end: 18 };
        return { start: 1, end: 6 };
    }

    async function refreshDisplay() {
        let res = await fetch('/api/status');
        let data = await res.json();

        document.getElementById('stat-total').innerText = data.total_slots;
        document.getElementById('stat-avail').innerText = data.available_slots;
        document.getElementById('stat-occ').innerText = data.occupied_slots;

        let activeRes = await fetch('/api/active-vehicles');
        let activeVehicles = await activeRes.json();

        // Render Zone Floor Map with Specified Color Scheme
        let grid = document.getElementById('slots-grid');
        grid.innerHTML = '';
        let range = getZoneRange(currentZone);

        for(let i = range.start; i <= range.end; i++) {
            let cell = document.createElement('div');
            let parkedCar = activeVehicles.find(v => v.slot_id === i);
            let isTaken = !!parkedCar;
            let isSelected = selectedSlotId === i;

            cell.className = 'slot-cell ' + (isTaken ? 'taken' : 'open') + (isSelected ? ' active-selected' : '');
            cell.onclick = () => selectSlot(i, parkedCar ? parkedCar.plate : null);

            cell.innerHTML = `
                <div class="slot-number">${currentZone}${i - range.start + 1}</div>
                ${isTaken ? `
                    <div class="car-icon"></div>
                    <div class="slot-plate">${parkedCar.plate}</div>
                ` : `<span style="color:var(--slot-open); font-size:0.8rem; font-weight:700;">OPEN</span>`}
            `;
            grid.appendChild(cell);
        }

        // Render Active Table
        let tableBody = document.getElementById('active-table-body');
        document.getElementById('active-count').innerText = activeVehicles.length + ' Parked';

        if(activeVehicles.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-sub);">No active parked vehicles</td></tr>`;
        } else {
            tableBody.innerHTML = activeVehicles.map(v => {
                let zoneLetter = v.slot_id <= 6 ? 'A' : (v.slot_id <= 12 ? 'B' : 'C');
                let localNum = v.slot_id <= 6 ? v.slot_id : (v.slot_id <= 12 ? v.slot_id - 6 : v.slot_id - 12);
                return `
                    <tr>
                        <td><b>${v.plate}</b></td>
                        <td>Zone ${zoneLetter}-${localNum}</td>
                        <td>${v.entry_time_formatted.split(' ')[1]}</td>
                        <td><b>Kshs. ${v.est_fee}</b> (${v.duration_minutes}m)</td>
                        <td><button class="pill-btn" style="background:#e2e8f0; padding:0.25rem 0.75rem;" onclick="selectSlot(${v.slot_id}, '${v.plate}')">Checkout</button></td>
                    </tr>
                `;
            }).join('');
        }
    }

    async function recordEntry() {
        let plate = document.getElementById('entry-plate').value.trim();
        if(!plate) return alert('Please enter a license plate!');

        let res = await fetch('/api/entry', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({plate: plate})
        });
        let data = await res.json();
        if(data.error) {
            alert(data.error);
        } else {
            document.getElementById('entry-plate').value = '';
            refreshDisplay();
        }
    }

    async function calculateFee() {
        let plate = document.getElementById('exit-plate').value.trim();
        if(!plate) return alert('Please enter a license plate!');

        let res = await fetch('/api/calculate-fee?plate=' + encodeURIComponent(plate));
        let data = await res.json();
        if(data.error) { alert(data.error); return; }

        document.getElementById('bill-duration').innerText = data.duration_minutes + ' Mins';
        document.getElementById('bill-amount').innerText = data.fee_ksh;
        document.getElementById('checkout-panel').style.display = 'block';
    }

    async function processPayment(method) {
        let plate = document.getElementById('exit-plate').value.trim();
        let res = await fetch('/api/exit-pay', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({plate: plate, method: method})
        });
        let data = await res.json();
        if(data.barrier_opened) {
            alert('Payment Confirmed! Barrier Opened for ' + plate);
            document.getElementById('checkout-panel').style.display = 'none';
            document.getElementById('exit-plate').value = '';
            selectedSlotId = null;
            refreshDisplay();
        }
    }

    async function resetSystem() {
        if(confirm("Are you sure you want to reset all records?")) {
            await fetch('/api/reset-all', { method: 'POST' });
            selectedSlotId = null;
            refreshDisplay();
        }
    }

    setInterval(refreshDisplay, 5000);
    refreshDisplay();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    return jsonify(lot.check_availability())

@app.route('/api/active-vehicles')
def active_vehicles():
    vehicles = []
    for plate, session in lot.active_sessions.items():
        fee_info = lot.calculate_fee_for_plate(plate)
        entry_dt = datetime.datetime.fromtimestamp(session.entry_time)
        vehicles.append({
            "plate": plate,
            "slot_id": session.slot_id,
            "entry_time_formatted": entry_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": fee_info["duration_minutes"],
            "est_fee": fee_info["fee_ksh"]
        })
    return jsonify(sorted(vehicles, key=lambda x: x["slot_id"]))

@app.route('/api/entry', methods=['POST'])
def entry():
    data = request.json or {}
    plate = data.get('plate', '').strip()
    if not plate:
        return jsonify({"error": "Please enter a valid license plate number!"}), 400
    try:
        res = lot.vehicle_entry(plate)
        return jsonify({"message": f"Assigned to Bay {res['slot_id']}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/calculate-fee')
def calc_fee():
    plate = request.args.get('plate', '').strip()
    if not plate:
        return jsonify({"error": "License plate required"}), 400
    try:
        return jsonify(lot.calculate_fee_for_plate(plate))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/exit-pay', methods=['POST'])
def exit_pay():
    data = request.json or {}
    plate = data.get('plate', '').strip()
    try:
        res = lot.vehicle_exit_and_pay(plate, data.get('method', 'M-Pesa'))
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/reset-all', methods=['POST'])
def reset_all():
    lot.reset_database()
    return jsonify({"message": "System reset successfully"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)