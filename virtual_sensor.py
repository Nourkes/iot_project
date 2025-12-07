"""
Simulation de capteur IoT COMPLÈTE - SANS compte AWS
Utilise un broker MQTT local (Mosquitto) pour démonstration

AVANTAGES:
- Aucun compte cloud nécessaire
- Aucune carte bancaire
- Démo 100% locale et gratuite
- Concept identique à AWS IoT Core
"""

import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt # type: ignore

# Configuration MQTT LOCAL (broker Mosquitto local)
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
CLIENT_ID = "virtual_sensor_001"
TOPIC_TELEMETRY = "sensors/temperature/data"
TOPIC_COMMAND = "sensors/temperature/command"

# Variables de simulation
current_temperature = 22.0
current_humidity = 50.0
device_status = "online"
sampling_interval = 5  # secondes


class VirtualSensor:
    """Classe représentant un capteur IoT virtuel"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback de connexion"""
        if rc == 0:
            print(f"[{datetime.now()}] ✓ Connecté au broker MQTT local!")
            self.is_connected = True
            
            # S'abonner au topic de commande
            self.client.subscribe(TOPIC_COMMAND)
            print(f"[{datetime.now()}] ✓ Abonné au topic: {TOPIC_COMMAND}")
        else:
            print(f"[{datetime.now()}] ❌ Échec de connexion: Code {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback de déconnexion"""
        self.is_connected = False
        print(f"[{datetime.now()}] ⚠️  Déconnecté du broker")
        
    def command_callback(self, client, userdata, message):
        """Callback appelé lors de la réception d'une commande"""
        global sampling_interval, device_status
        
        print(f"\n[{datetime.now()}] 📥 Commande reçue sur {message.topic}")
        try:
            payload = json.loads(message.payload.decode('utf-8'))
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Traiter la commande
            if "action" in payload:
                action = payload["action"]
                
                if action == "set_interval":
                    new_interval = payload.get("value", 5)
                    sampling_interval = new_interval
                    print(f"✓ Intervalle d'échantillonnage mis à jour: {sampling_interval}s")
                    
                elif action == "reboot":
                    print("✓ Simulation de redémarrage de l'appareil...")
                    device_status = "rebooting"
                    time.sleep(2)
                    device_status = "online"
                    print("✓ Appareil redémarré")
                    
                elif action == "shutdown":
                    print("✓ Arrêt de l'appareil demandé")
                    device_status = "offline"
        except Exception as e:
            print(f"❌ Erreur traitement commande: {e}")
        
    def connect(self):
        """Établit la connexion MQTT avec le broker local"""
        print(f"[{datetime.now()}] Initialisation du client MQTT...")
        
        # Initialiser le client MQTT
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.command_callback
        
        # Connexion au broker
        print(f"[{datetime.now()}] Connexion à {MQTT_BROKER}:{MQTT_PORT}...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print(f"\n❌ ERREUR DE CONNEXION: {e}")
            print("\n💡 SOLUTION: Installez et démarrez Mosquitto:")
            print("   Windows: https://mosquitto.org/download/")
            print("   Linux: sudo apt-get install mosquitto")
            print("   Mac: brew install mosquitto")
            print("\n   Ou utilisez un broker public: test.mosquitto.org")
            raise
    
    def generate_telemetry(self):
        """Génère des données de télémétrie simulées"""
        global current_temperature, current_humidity
        
        # Simuler des variations réalistes
        current_temperature += random.uniform(-0.5, 0.5)
        current_temperature = max(15.0, min(35.0, current_temperature))
        
        current_humidity += random.uniform(-2.0, 2.0)
        current_humidity = max(30.0, min(80.0, current_humidity))
        
        telemetry = {
            "device_id": CLIENT_ID,
            "timestamp": datetime.now().isoformat(),
            "temperature": round(current_temperature, 2),
            "humidity": round(current_humidity, 2),
            "status": device_status,
            "battery": random.randint(85, 100),
            "signal_strength": random.randint(-70, -30)
        }
        
        return telemetry
    
    def publish_telemetry(self):
        """Publie les données de télémétrie"""
        if not self.is_connected:
            print("❌ Non connecté, impossible de publier")
            return
        
        telemetry = self.generate_telemetry()
        message_json = json.dumps(telemetry)
        
        print(f"\n[{datetime.now()}] 📤 Publication des données:")
        print(f"  Temperature: {telemetry['temperature']}°C")
        print(f"  Humidity: {telemetry['humidity']}%")
        print(f"  Status: {telemetry['status']}")
        
        self.client.publish(TOPIC_TELEMETRY, message_json, qos=1)
        
    def run(self):
        """Boucle principale du capteur"""
        try:
            self.connect()
            
            # Démarrer la boucle réseau
            self.client.loop_start()
            
            # Attendre la connexion
            timeout = 5
            while not self.is_connected and timeout > 0:
                time.sleep(1)
                timeout -= 1
            
            if not self.is_connected:
                print("❌ Impossible de se connecter au broker")
                return
            
            print(f"\n{'='*60}")
            print(f"🌡️  Capteur virtuel démarré - Envoi toutes les {sampling_interval}s")
            print(f"Topic telemetry: {TOPIC_TELEMETRY}")
            print(f"Topic command: {TOPIC_COMMAND}")
            print("Appuyez sur Ctrl+C pour arrêter")
            print(f"{'='*60}\n")
            
            while device_status != "offline":
                self.publish_telemetry()
                time.sleep(sampling_interval)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                print(f"[{datetime.now()}] Déconnecté")


if __name__ == "__main__":
    print("="*60)
    print("🚀 CAPTEUR IoT VIRTUEL - Mode Local (Sans AWS)")
    print("="*60)
    print("\n📌 Configuration:")
    print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Topics: {TOPIC_TELEMETRY}, {TOPIC_COMMAND}")
    print("\n💡 Pour recevoir les messages, ouvrez un autre terminal:")
    print("   python mqtt_subscriber.py")
    print("\n" + "="*60 + "\n")
    
    sensor = VirtualSensor()
    sensor.run()