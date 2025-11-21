import asyncio
import logging
from typing import Optional

from bleak import BleakScanner, BleakClient

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

# Optional fixed MAC you *think* the scale uses
STATIC_SCALE_MAC_ADDRESS = "FF:FF:00:20:5C:33"

# Hints used to identify the scale by its BLE name.
# You can adjust these based on what you see in scan_scale.py output.
SCALE_NAME_HINTS = [
    "LYE",
    "SCALE",
    "ELINK",
    "AILINK"
]

# Characteristic UUID you told me about
WEIGHT_CHAR_UUID = "0000f0a0-0000-1000-8000-00805f9b34fb"

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)


# -------------------------------------------------------------------
# DISCOVERY HELPERS
# -------------------------------------------------------------------

async def find_scale_address_by_name(timeout: float = 10.0) -> Optional[str]:
    """
    Scan for BLE devices and try to find the scale by its name,
    using SCALE_NAME_HINTS as matching patterns.
    """
    logging.info("Scanning for BLE devices (timeout %.1fs)...", timeout)
    devices = await BleakScanner.discover(timeout=timeout)

    if not devices:
        logging.warning("No BLE devices found during scan.")
        return None

    logging.info("Devices found:")
    for d in devices:
        logging.info("  %s | %s | RSSI=%s", d.address, d.name, d.rssi)

    for d in devices:
        name = (d.name or "").upper()
        if any(hint in name for hint in SCALE_NAME_HINTS):
            logging.info("Using device %s (%s) as the scale.", d.address, d.name)
            return d.address

    logging.warning("No device matched the SCALE_NAME_HINTS: %s", SCALE_NAME_HINTS)
    return None


async def resolve_scale_address() -> Optional[str]:
    """
    Decide which address to use:
    1) First try to discover by name.
    2) If that fails but a static MAC is configured, fall back to it.
    """
    # 1) Try to discover dynamically
    discovered_address = await find_scale_address_by_name()
    if discovered_address:
        return discovered_address

    # 2) Fallback to static MAC if provided
    if STATIC_SCALE_MAC_ADDRESS:
        logging.info(
            "Falling back to static MAC address: %s",
            STATIC_SCALE_MAC_ADDRESS
        )
        return STATIC_SCALE_MAC_ADDRESS

    logging.error("No scale address could be resolved.")
    return None


# -------------------------------------------------------------------
# CORE READER
# -------------------------------------------------------------------

async def read_weight_once() -> Optional[float]:
    """
    Try to read a single weight value from the scale.

    Returns:
        float weight in kg, or None if not available.
    """
    attempt = 0

    while attempt < MAX_RETRIES:
        attempt += 1
        logging.info("Attempt %d/%d to read from scale...", attempt, MAX_RETRIES)

        try:
            address = await resolve_scale_address()
            if not address:
                logging.error("No valid address for the scale (discovery + static failed).")
                return None

            logging.info("Connecting to scale at address %s ...", address)

            async with BleakClient(address, timeout=15.0) as client:
                if not client.is_connected:
                    logging.error("Unable to connect to the scale at %s", address)
                    return None

                logging.info("Connected. Reading characteristic %s ...", WEIGHT_CHAR_UUID)

                data = await client.read_gatt_char(WEIGHT_CHAR_UUID)
                logging.info("Raw data from characteristic: %s", data.hex(" "))

                if not data:
                    logging.error("No data received from scale.")
                    return None

                # Parse according to your assumption: little-endian int / 10.0
                raw_value = int.from_bytes(data, byteorder="little", signed=False)
                kg = raw_value / 10.0

                logging.info("Parsed weight: %.1f kg", kg)
                return kg

        except Exception as e:
            logging.error(
                "Error reading from Bluetooth scale (attempt %d/%d): %s",
                attempt, MAX_RETRIES, e
            )
            if attempt < MAX_RETRIES:
                logging.info("Retrying in %d seconds...", RETRY_DELAY)
                await asyncio.sleep(RETRY_DELAY)
            else:
                logging.error("Max retries reached. Could not read from the scale.")
                return None


async def get_weight() -> float:
    """
    Public async function used by your Flask endpoint.

    Raises RuntimeError if reading fails.
    """
    weight = await read_weight_once()
    if weight is None:
        raise RuntimeError("Failed to read weight from Bluetooth scale.")
    return weight


# -------------------------------------------------------------------
# DIRECT TEST (run this file by itself)
# -------------------------------------------------------------------
if __name__ == "__main__":
    async def _test():
        try:
            kg = await get_weight()
            print(f"✅ Weight from scale: {kg:.1f} kg")
        except Exception as e:
            print("❌ Could not read weight:", e)

    asyncio.run(_test())
