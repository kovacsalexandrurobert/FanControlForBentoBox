import json
import time
import sys
from display_service import DisplayService
from InitService import InitService
from os import uname

# Global BLE instance for cleanup
ble_instance = None

def check_development_mode():
    """Check if we should wait for development mode"""
    try:
        # Check if development mode file exists
        try:
            with open("dev_mode.txt", "r") as f:
                dev_mode = f.read().strip().lower()
                if dev_mode in ['true', '1', 'yes', 'on']:
                    print("🔧 Development Mode Detected")
                    print("⏸️  Boot paused for development...")
                    print("   Connect with Thonny and run: import boot; boot.main()")
                    print("   Or delete dev_mode.txt and restart for normal operation")
                    
                    # Wait indefinitely for development
                    while True:
                        time.sleep(1)
        except OSError:
            # dev_mode.txt doesn't exist, proceed normally
            pass
        
        # Normal operation - just a short delay
        print("🔧 Starting in 2 seconds...")
        print("   (Create 'dev_mode.txt' file to pause for development)")
        time.sleep(2)
        return True
            
    except Exception as e:
        print(f"⚠️  Development check failed: {e}")
        print("⏰ Proceeding with automatic start...")
        return True

def main():
    """Main boot function that can be interrupted with Ctrl+C"""
    global ble_instance
    
    with open("config.json") as f:
        config = json.load(f)
    userCfg = {}
    isInitialised = False 
    connection_state = False
    displayCfg = config.get('display')
    
    # Initialize display service with error handling
    try:
        display = DisplayService(connection_state, displayCfg)
        print("✅ Display service initialized successfully")
    except Exception as e:
        print(f"❌ Display service initialization failed: {e}")
        print("   Continuing without display...")
        display = None
    
    try: 
        with open("userConfig.json") as f:
            userCfg = json.load(f)
            isInitialised = True
            print("✅ User configuration loaded successfully")
            print("   User ID:", userCfg.get('userID', 'Not set'))
            print("   Device ID:", userCfg.get('deviceId', 'Not set'))
            print("   Splash Logo:", userCfg.get('splashLogo', 'Default'))
            print("   Initialized:", userCfg.get('is_initialized', False))
    except Exception as error:
        print("❌ No User Config found:", error)
        print("   Continue Device Setup!")

    splashLogo = userCfg.get('splashLogo') or config['display']['splashLogo']    
    # Display the splash screen (if display is available)
    if display is not None:
        try:
            display.displayProgressBar(displayCfg, '', splashLogo, True )
            display.clearDisplay()
        except Exception as e:
            print(f"❌ Error displaying splash screen: {e}")
    else:
        print("⚠️  Display not available, skipping splash screen")

    # Check if we have extended network and Bluetooth LE capabilities with Pi Pico W if not we continue with basic capabilities.
    if uname()[4] == 'Raspberry Pi Pico W with RP2040':
        print('RPi Pico W')   # True
        if(isInitialised == False):
            # Create BLE instance and BLESimplePeripheral for device setup
            import bluetooth
            import machine
            import ubinascii
            # Get unique device ID (last 4 characters of flash ID)
            flash_id = ubinascii.hexlify(machine.unique_id()).decode()
            device_uuid = flash_id[-4:].upper()
            name = f"SmartBento-{device_uuid}"
            print(f"🔧 Generated device name: {name}")
            print(f"   Flash ID: {flash_id}")
            print(f"   Device UUID: {device_uuid}")
            from ble_simple_peripheral import BLESimplePeripheral
            
            try:
                ble_instance = bluetooth.BLE()
                print("🚀 BLE object created.")
                
                # Activate BLE first
                ble_instance.active(True)
                print("🚀 BLE activated.")
                
                # Small delay to ensure BLE is properly initialized
                time.sleep(0.1)
                
                # Verify BLE is active
                if not ble_instance.active():
                    raise Exception("BLE failed to activate")
                print("✅ BLE activation verified")
                
                # Try to configure GAP name (optional)
                try:
                    ble_instance.config(gap_name=name)
                    print("🚀 BLE GAP name configured.")
                except Exception as config_error:
                    print(f"⚠️  BLE GAP name config warning: {config_error}")
                    print("   Continuing without GAP name configuration...")
                
                sp = BLESimplePeripheral(ble_instance, name)
                print("🚀 BLE simple peripheral started.")
                InitService(sp)
                print("🚀 BLE InitService started. Press Ctrl+C to stop.")
            except Exception as e:
                print(f"❌ BLE initialization failed: {e}")
                print("   Continuing without BLE...")
                # Ensure BLE is deactivated if there was an error
                try:
                    if ble_instance and ble_instance.active():
                        ble_instance.active(False)
                        print("   BLE deactivated due to error")
                except:
                    pass

    else:
    #     TO DO implement splashLogo selection with internal button. No WiFi or Bluetooth LE capabilities available.
        print('RPi Pico')     # False

if __name__ == "__main__":
    try:
        # Development mode check - gives you time to connect with Thonny
        check_development_mode()
        
        print("🔧 Starting SmartBento Device Boot Process...")
        print("   Press Ctrl+C to stop execution")
        main()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(0.1)  # Shorter sleep for more responsive interrupt handling
        except KeyboardInterrupt:
            raise  # Re-raise the KeyboardInterrupt to be caught by outer try-catch
            
    except KeyboardInterrupt:
        print("\n🛑 Boot process interrupted by user (Ctrl+C)")
        print("   Shutting down gracefully...")
        
        # Clean up any resources if needed
        try:
            # Stop BLE if it was started
            if ble_instance and ble_instance.active():
                print("   Stopping BLE...")
                ble_instance.active(False)
        except:
            pass
            
        print("   Boot process stopped successfully")
        print("   Run 'main.py' to start the main application")
        
    except Exception as e:
        print(f"\n❌ Unexpected error during boot: {e}")
        print("   Boot process failed")


