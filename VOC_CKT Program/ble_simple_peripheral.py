# This example demonstrates a UART periperhal.
import bluetooth
import random
import struct
import time
import machine
import ubinascii
from ble_advertising import advertising_payload

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

# SmartBento custom service UUID
_SMARTBENTO_UUID = bluetooth.UUID("A1B2C3D4-E5F6-7890-ABCD-EF1234567890")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _SMARTBENTO_UUID,
    (_UART_TX, _UART_RX),
)


# Get unique device ID (last 4 characters of flash ID)
flash_id = ubinascii.hexlify(machine.unique_id()).decode()
device_uuid = flash_id[-4:].upper()
name = f"SmartBento-{device_uuid}"
print(f"🔧 Generated device name: {name}")
print(f"   Flash ID: {flash_id}")
print(f"   Device UUID: {device_uuid}")

class BLESimplePeripheral:
    def __init__(self, ble, name=None):
        self._ble = ble
        self._connections = set()
        self._write_callback = None
        
        try:
            # Set up BLE interrupt handler
            self._ble.irq(self._irq)
            print("✅ BLE interrupt handler set")
            
            # Register GATT services
            ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
            print("✅ GATT services registered")
            
            # Set buffer size (if supported)
            try:
                self._ble.gatts_set_buffer(self._handle_rx, 517)
                print("✅ GATT buffer configured")
            except Exception as buffer_error:
                print(f"⚠️  GATT buffer config warning: {buffer_error}")
                print("   Continuing with default buffer size...")
            
        except Exception as e:
            print(f"❌ BLE peripheral setup failed: {e}")
            raise e
        
        # Generate device name: SmartBento + 4-letter UUID
        if name is None:
            # Get unique device ID (last 4 characters of flash ID)
            flash_id = ubinascii.hexlify(machine.unique_id()).decode()
            device_uuid = flash_id[-4:].upper()
            name = f"SmartBento-{device_uuid}"
            print(f"🔧 Generated device name: {name}")
            print(f"   Flash ID: {flash_id}")
            print(f"   Device UUID: {device_uuid}")
        else:
            print(f"🔧 Using provided device name: {name}")
        
        print(f"📡 Setting up BLE advertising with name: {name}")
        print(f"🔧 Using service UUID: {_SMARTBENTO_UUID}")
        try:
            # Try simple advertising first (just name, no services)
            print("🔧 Creating simple advertising payload (name only)")
            self._payload = advertising_payload(name=name, services=None)
            print("✅ Simple advertising payload created")
            
            # Use standard advertising interval for better compatibility
            self._advertise(interval_us=500000)  # 500ms interval (more standard)
            print("✅ BLE advertising started (simple mode)")
            
            # Wait a bit, then try with services
            import time
            time.sleep(3)
            
            print("🔧 Creating full advertising payload (with services)")
            self._payload = advertising_payload(name=name, services=[_SMARTBENTO_UUID])
            print("✅ Full advertising payload created")
            self._advertise(interval_us=500000)  # 500ms interval
            print("✅ BLE advertising updated (full mode)")
            
            # Start a background task to monitor advertising
            import _thread
            _thread.start_new_thread(self._monitor_advertising, ())
            
        except Exception as e:
            print(f"❌ BLE advertising setup failed: {e}")
            raise e

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            print(f"📤 Remaining connections: {self._connections}")
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            print(f"📥 BLE write event - conn_handle: {conn_handle}, value_handle: {value_handle}")
            value = self._ble.gatts_read(value_handle)
            print(f"📥 BLE data received: {value}")
            if value_handle == self._handle_rx and self._write_callback:
                print(f"📥 Calling write callback with data: {value}")
                self._write_callback(value)
            else:
                print(f"⚠️  Write callback not called - value_handle: {value_handle}, _handle_rx: {self._handle_rx}, callback: {self._write_callback is not None}")

    def send(self, data):
        print(f"📤 Attempting to send data: {data}")
        print(f"📤 Active connections: {self._connections}")
        for conn_handle in self._connections:
            try:
                self._ble.gatts_notify(conn_handle, self._handle_tx, data)
                print(f"📤 Data sent successfully to connection {conn_handle}")
            except Exception as e:
                print(f"❌ Failed to send data to connection {conn_handle}: {e}")

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=100000):  # Faster advertising interval
        try:
            print("Starting advertising")
            print(f"   Advertising interval: {interval_us}μs")
            print(f"   Payload length: {len(self._payload)} bytes")
            print(f"   Payload data: {self._payload.hex()}")
            
            # Check if BLE is still active before advertising
            if not self._ble.active():
                print("❌ BLE is not active, cannot advertise")
                raise Exception("BLE not active")
            
            # Try basic advertising first (more compatible)
            self._ble.gap_advertise(interval_us, adv_data=self._payload)
            print("✅ BLE advertising started successfully")
            
            # Verify advertising is actually running
            time.sleep(0.1)
            print("✅ BLE advertising verification complete")
            
        except Exception as e:
            print(f"❌ Failed to start BLE advertising: {e}")
            print(f"   BLE active status: {self._ble.active()}")
            raise e

    def on_write(self, callback):
        self._write_callback = callback
    
    def _monitor_advertising(self):
        """Monitor BLE advertising status in background"""
        import time
        while True:
            time.sleep(5)  # Check every 5 seconds
            if not self._ble.active():
                print("⚠️  BLE became inactive, attempting to restart advertising...")
                try:
                    self._ble.active(True)
                    time.sleep(0.1)
                    self._advertise(interval_us=500000)
                    print("✅ BLE advertising restarted")
                except Exception as e:
                    print(f"❌ Failed to restart BLE advertising: {e}")
            # BLE is active, no need to log every check


def demo():
    ble = bluetooth.BLE()
    # Remove unsupported config parameter
    p = BLESimplePeripheral(ble)

    def on_rx(v):
        print("RX", v)

    p.on_write(on_rx)

    i = 0
    while True:
        if p.is_connected():
            # Short burst of queued notifications.
            for _ in range(3):
                data = str(i) + "_"
                print("TX", data)
                p.send(data)
                i += 1
        time.sleep_ms(100)


if __name__ == "__main__":
    demo()