import time
from parking_system import ParkingLot, VehicleType


def main():
    vehicle_types = [
        VehicleType(id=1, name="Car", hourly_rate=50),
        VehicleType(id=2, name="Motorcycle", hourly_rate=20),
        VehicleType(id=3, name="Truck", hourly_rate=100),
    ]

    lot = ParkingLot(total_slots=5, vehicle_types=vehicle_types, db_path="parking_lot.db")

    print("Initial availability:", lot.check_availability())

    slot = lot.vehicle_entry("KDA 123B", vehicle_type_id=1)
    print(f"\nKDA 123B (Car) entered -> assigned slot: {slot}")
    print("Availability now:", lot.check_availability())

    slot2 = lot.vehicle_entry("KDA 456C", vehicle_type_id=2)
    print(f"\nKDA 456C (Motorcycle) entered -> assigned slot {slot2}")
    print("Availability now:", lot.check_availability())

    print("\n...time passes...")
    time.sleep(2)

    result = lot.vehicle_exit("KDA 123B")
    print("\nKDA 123B exited", result)
    print("Availability now:", lot.check_availability())

    lot.close()

if __name__ == "__main__":
    main()