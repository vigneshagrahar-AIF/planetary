import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for BLE devices... stand on / wake up the scale!")
    devices = await BleakScanner.discover(timeout=10.0)
    for d in devices:
        print(f"{d.address}  |  {d.name}  |  RSSI={d.rssi}")

asyncio.run(main())
