from bleak import BleakClient
import logging
import asyncio

SCALE_MAC_ADDRESS = "FF:FF:00:20:5C:33"  # Bluetooth MAC address for LYE scale
WEIGHT_CHAR_UUID = "0000f0a0-0000-1000-8000-00805f9b34fb"  # Scale's weight characteristic UUID

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Function to read weight from scale asynchronously
async def read_weight_once():
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            async with BleakClient(SCALE_MAC_ADDRESS) as client:
                if not await client.is_connected():
                    logging.error(f"Unable to connect to the scale: {SCALE_MAC_ADDRESS}")
                    return None
                data = await client.read_gatt_char(WEIGHT_CHAR_UUID)
                raw_value = int.from_bytes(data, byteorder="little")
                kg = raw_value / 10.0  # Assuming the scale returns weight in hectograms
                return kg
        except Exception as e:
            logging.error(f"Error reading from Bluetooth scale (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            attempt += 1
            if attempt < MAX_RETRIES:
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logging.error("Max retries reached. Could not read from the scale.")
                raise RuntimeError("Failed to read weight from scale after multiple attempts.")

# Function to get the weight, which calls `read_weight_once`
async def get_weight():
    weight = await read_weight_once()  # Await the async function
    if weight is None:
        raise RuntimeError("Failed to read weight from Bluetooth scale.")
    return weight
