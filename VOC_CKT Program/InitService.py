import json
import time
from ble_simple_peripheral import BLESimplePeripheral

class InitService:
    def __init__(self, blePeripheral: BLESimplePeripheral):
        self.blePeripheral = blePeripheral
        self.setupBLE()

    def setupBLE(self):
        # Set up the callback for when data is received
        self.blePeripheral.on_write(self.on_rx)
        print("✅ InitService initialized and ready to receive data")

    def on_rx(self, data):
        """Handle incoming data from Android app"""
        try:
            print(f"🔍 InitService.on_rx called with data: {data}")
            # Decode the received data
            message = data.decode('utf-8')
            print(f"Data received: {data}")
            print(f"Decoded message: {message}")
            
            # Parse the JSON message
            config = json.loads(message)
            print(f"Received config: {config}")
            
            # Handle different message types
            if config.get('type') == 'wifi_config':
                print("WiFi config received - SSID:", config.get('ssid'), "Security:", config.get('security'))
                self.handleWiFiConfig(config.get('ssid'), config.get('password'), config.get('security'))
                return
            elif config.get('type') == 'splash_logo_config':
                print("Splash logo config received - Logo ID:", config.get('logoId'), "Name:", config.get('logoName'))
                self.handleSplashLogoConfig(config.get('logoId'), config.get('logoName'))
                return
            elif config.get('userID') and config.get('deviceId'):
                print(f"Bind message received - userID: {config.get('userID')} deviceId: {config.get('deviceId')}")
                self.createUserConfig(config.get('userID'), config.get('deviceId'))
                return
            elif config.get('connectionSuccess'):
                print("Connection success message received")
                return
            elif config.get('type') == 'request_splash_logos':
                print("Splash logos request received")
                self.sendAvailableSplashLogos()
                return
            elif config.get('type') == 'request_sensor_data':
                print("Sensor data request received")
                self.sendSensorData()
                return
            elif config.get('type') == 'fan_control':
                print("Fan control command received")
                self.handleFanControl(config.get('action'))
                return
            elif config.get('type') == 'device_settings':
                print("Device settings received")
                self.handleDeviceSettings(config.get('settings'))
                return
            else:
                print("Unknown message type received")
                
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def createUserConfig(self, userID, deviceId):
        """Create or update user configuration file"""
        try:
            # Try to read existing config
            try:
                with open("userConfig.json", "r") as f:
                    user_config = json.load(f)
                    print("📖 Existing userConfig.json loaded")
            except OSError:
                # Create new config if file doesn't exist
                user_config = {
                    "userID": userID,
                    "deviceId": deviceId,
                    "bound_at": time.time(),
                    "last_updated": time.time(),
                    "wifi_configured": False,
                    "splash_logo_configured": False
                }
                print("📝 Created new user configuration")

            # Update with new binding info
            user_config["userID"] = userID
            user_config["deviceId"] = deviceId
            user_config["bound_at"] = time.time()
            user_config["last_updated"] = time.time()

            # Save updated configuration
            with open("userConfig.json", "w") as f:
                json.dump(user_config, f)
            
            print("✅ User configuration saved to userConfig.json")
            
            # Send success response back to Android app
            success_response = {
                "type": "bind_response",
                "status": "success",
                "message": "Device bound successfully",
                "userID": userID,
                "deviceId": deviceId,
                "bound_at": user_config["bound_at"]
            }
            self.blePeripheral.send(json.dumps(success_response))
            print("📤 Sent bind_response to Android app")
            
        except Exception as e:
            print(f"Error creating user config: {e}")
            # Send error response
            error_response = {
                "type": "bind_response",
                "status": "error",
                "message": f"Failed to create user config: {str(e)}"
            }
            self.blePeripheral.send(json.dumps(error_response))

    def handleWiFiConfig(self, ssid, password, security):
        """Handle WiFi configuration from Android app and save to userConfig.json"""
        try:
            # Read existing user config or create new one
            try:
                with open("userConfig.json", "r") as f:
                    user_config = json.load(f)
                    print("📖 Loaded existing userConfig.json for WiFi config")
            except OSError:
                # Create basic config if file doesn't exist
                user_config = {
                    "userID": "unknown",
                    "deviceId": "unknown",
                    "bound_at": time.time(),
                    "last_updated": time.time(),
                    "wifi_configured": False,
                    "splash_logo_configured": False
                }
                print("📝 Created new user configuration for WiFi config")

            # Update WiFi configuration
            user_config['wifi_config'] = {
                'ssid': ssid,
                'password': password,
                'security': security,
                'configured_at': time.time(),
                'configured_by': user_config.get('userID', 'unknown')
            }
            
            # Mark as WiFi configured
            user_config['wifi_configured'] = True
            user_config['last_updated'] = time.time()
            
            # Save updated configuration
            with open("userConfig.json", "w") as f:
                json.dump(user_config, f)
            
            print("✅ WiFi configuration saved to userConfig.json")
            
            # Read back the saved config to verify
            with open("userConfig.json", "r") as f:
                saved_config = json.load(f)
                wifi_cfg = saved_config.get('wifi_config', {})
            
            # Send success response back to Android app
            success_response = {
                'type': 'wifi_config_response',
                'status': 'success',
                'message': 'WiFi configuration saved successfully',
                'ssid': ssid,
                'security': security,
                'configured_at': wifi_cfg.get('configured_at')
            }
            self.blePeripheral.send(json.dumps(success_response))
            print("📤 Sent wifi_config_response to Android app")
            
        except Exception as e:
            print(f"❌ Error handling WiFi config: {e}")
            # Send error response
            error_response = {
                'type': 'wifi_config_response',
                'status': 'error',
                'message': f'Failed to save WiFi config: {str(e)}'
            }
            self.blePeripheral.send(json.dumps(error_response))

    def handleSplashLogoConfig(self, logoId, logoName):
        """Handle splash logo configuration from Android app and save to userConfig.json"""
        try:
            # Read existing user config or create new one
            try:
                with open("userConfig.json", "r") as f:
                    user_config = json.load(f)
                    print("📖 Loaded existing userConfig.json for splash logo config")
            except OSError:
                # Create basic config if file doesn't exist
                user_config = {
                    "userID": "unknown",
                    "deviceId": "unknown",
                    "bound_at": time.time(),
                    "last_updated": time.time(),
                    "wifi_configured": False,
                    "splash_logo_configured": False
                }
                print("📝 Created new user configuration for splash logo config")

            # Update splash logo configuration
            user_config['splash_logo_config'] = {
                'logoId': logoId,
                'logoName': logoName,
                'configured_at': time.time(),
                'configured_by': user_config.get('userID', 'unknown')
            }
            
            # Mark as splash logo configured
            user_config['splash_logo_configured'] = True
            user_config['last_updated'] = time.time()
            
            # Save updated configuration
            with open("userConfig.json", "w") as f:
                json.dump(user_config, f)
            
            print(f"✅ Splash logo configuration saved: {logoName} (ID: {logoId})")
            
            # Read back the saved config to verify
            with open("userConfig.json", "r") as f:
                saved_config = json.load(f)
                logo_cfg = saved_config.get('splash_logo_config', {})
            
            # Send success response back to Android app
            success_response = {
                'type': 'splash_logo_response',
                'status': 'success',
                'message': f'Splash logo "{logoName}" set successfully',
                'logoId': logoId,
                'logoName': logoName,
                'configured_at': logo_cfg.get('configured_at')
            }
            self.blePeripheral.send(json.dumps(success_response))
            print("📤 Sent splash_logo_response to Android app")
            
        except Exception as e:
            print(f"❌ Error handling splash logo config: {e}")
            # Send error response
            error_response = {
                'type': 'splash_logo_response',
                'status': 'error',
                'message': f'Failed to set splash logo: {str(e)}'
            }
            self.blePeripheral.send(json.dumps(error_response))

    def sendAvailableSplashLogos(self):
        """Send list of available splash logos to Android app"""
        try:
            from SplashLogos import Logos
            logos = Logos()
            
            # Get available logo names and IDs
            available_logos = [
                {'id': 'Bento', 'name': 'Bento'},
                {'id': 'Creality', 'name': 'Creality'},
                {'id': 'BambuLab', 'name': 'BambuLab'},
                {'id': 'Voron', 'name': 'Voron'},
                {'id': 'Prusa', 'name': 'Prusa'}
            ]
            
            response = {
                'type': 'splash_logos_list',
                'status': 'success',
                'logos': available_logos,
                'count': len(available_logos)
            }
            
            print(f"📤 Sending {len(available_logos)} available splash logos to Android app")
            self.blePeripheral.send(json.dumps(response))
            print("✅ Splash logos list sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending splash logos list: {e}")
            error_response = {
                'type': 'splash_logos_list',
                'status': 'error',
                'message': f'Failed to get splash logos: {str(e)}'
            }
            self.blePeripheral.send(json.dumps(error_response))

    def sendSensorData(self):
        """Send current sensor data to Android app"""
        try:
            # Import sensors here to avoid circular imports
            from Sensors import Sensors
            
            # Initialize sensors if not already done
            if not hasattr(self, 'sensors'):
                self.sensors = Sensors()
            
            # Get current sensor readings
            temperature = self.sensors.temperature
            humidity = self.sensors.humidity
            voc_value = getattr(self.sensors, 'voc_value', 0)  # Default to 0 if not available
            
            # Get fan status (this would need to be implemented in your fan control system)
            fan_status = getattr(self, 'fan_status', False)  # Default to False
            
            sensor_data = {
                'type': 'sensor_data',
                'status': 'success',
                'temperature': temperature,
                'humidity': humidity,
                'vocValue': voc_value,
                'fanStatus': fan_status,
                'timestamp': time.time()
            }
            
            print(f"📤 Sending sensor data - Temp: {temperature}°C, Humidity: {humidity}%, VOC: {voc_value}, Fan: {fan_status}")
            self.blePeripheral.send(json.dumps(sensor_data))
            print("✅ Sensor data sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending sensor data: {e}")
            error_response = {
                'type': 'sensor_data',
                'status': 'error',
                'message': f'Failed to get sensor data: {str(e)}'
            }
            self.blePeripheral.send(json.dumps(error_response))

    def handleFanControl(self, action):
        """Handle fan control commands from Android app"""
        try:
            print(f"🔧 Fan control command: {action}")
            
            # Here you would implement actual fan control
            # For now, we'll simulate it
            if action == 'on':
                fan_status = True
                print("🌪️ Fan turned ON")
            elif action == 'off':
                fan_status = False
                print("🌪️ Fan turned OFF")
            else:
                raise ValueError(f"Invalid fan action: {action}")
            
            # Store fan status
            self.fan_status = fan_status
            
            # Send response back to Android app
            response = {
                'type': 'fan_control_response',
                'status': 'success',
                'fanStatus': fan_status,
                'action': action,
                'timestamp': time.time()
            }
            
            print(f"📤 Sending fan control response: {response}")
            self.blePeripheral.send(json.dumps(response))
            print("✅ Fan control response sent successfully")
            
        except Exception as e:
            print(f"❌ Error handling fan control: {e}")
            error_response = {
                'type': 'fan_control_response',
                'status': 'error',
                'message': f'Failed to control fan: {str(e)}'
            }
            self.blePeripheral.send(json.dumps(error_response))

    def handleDeviceSettings(self, settings):
        """Handle device settings from Android app"""
        try:
            print(f"⚙️ Device settings received: {settings}")
            
            # Update device settings
            device_name = settings.get('deviceName', 'SmartBento Device')
            temperature_unit = settings.get('temperatureUnit', 'celsius')
            voc_threshold = settings.get('vocThreshold', 100)
            fan_enabled = settings.get('fanEnabled', True)
            
            print(f"📝 Updating device settings:")
            print(f"   Name: {device_name}")
            print(f"   Temperature Unit: {temperature_unit}")
            print(f"   VOC Threshold: {voc_threshold}")
            print(f"   Fan Auto Control: {fan_enabled}")
            
            # Store settings (you might want to save these to a file)
            self.device_settings = {
                'deviceName': device_name,
                'temperatureUnit': temperature_unit,
                'vocThreshold': voc_threshold,
                'fanEnabled': fan_enabled,
                'updated_at': time.time()
            }
            
            # Send response back to Android app
            response = {
                'type': 'settings_response',
                'status': 'success',
                'message': 'Device settings updated successfully',
                'settings': self.device_settings,
                'timestamp': time.time()
            }
            
            print(f"📤 Sending settings response: {response}")
            self.blePeripheral.send(json.dumps(response))
            print("✅ Settings response sent successfully")
            
        except Exception as e:
            print(f"❌ Error handling device settings: {e}")
            error_response = {
                'type': 'settings_response',
                'status': 'error',
                'message': f'Failed to update settings: {str(e)}'
            }
            self.blePeripheral.send(json.dumps(error_response))
        