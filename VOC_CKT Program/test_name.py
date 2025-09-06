#!/usr/bin/env python3
"""
Test script to verify device name generation
"""
import machine
import ubinascii

print("🧪 Testing device name generation...")

# Get unique device ID (last 4 characters of flash ID)
flash_id = ubinascii.hexlify(machine.unique_id()).decode()
device_uuid = flash_id[-4:].upper()
name = f"SmartBento{device_uuid}"

print(f"🔧 Generated device name: {name}")
print(f"   Flash ID: {flash_id}")
print(f"   Device UUID: {device_uuid}")
print(f"   Full name: {name}")

# Test the BLE advertising payload generation
from ble_advertising import advertising_payload
import bluetooth

# Test with our SmartBento name
test_name = "SmartBento-6C28"
test_uuid = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")

print(f"🔧 Testing advertising payload generation:")
print(f"   Name: {test_name}")
print(f"   UUID: {test_uuid}")
print()

# Generate the payload
payload = advertising_payload(name=test_name, services=[test_uuid])

print(f"📡 Generated payload:")
print(f"   Raw bytes: {payload}")
print(f"   Length: {len(payload)} bytes")
print()

# Decode to verify
from ble_advertising import decode_name, decode_services

decoded_name = decode_name(payload)
decoded_services = decode_services(payload)

print(f"🔍 Decoded payload:")
print(f"   Name: {decoded_name}")
print(f"   Services: {decoded_services}")
print()

# Show the structure byte by byte
print(f"📊 Payload structure:")
i = 0
while i < len(payload):
    length = payload[i]
    if i + 1 < len(payload):
        adv_type = payload[i + 1]
        data = payload[i + 2:i + length + 1]
        
        type_name = {
            0x01: "FLAGS",
            0x09: "NAME", 
            0x07: "UUID128"
        }.get(adv_type, f"TYPE_{adv_type}")
        
        print(f"   [{length:2d}][0x{adv_type:02X}][{type_name:6s}] {data}")
        i += length + 1
    else:
        break

print("✅ Test complete!")
