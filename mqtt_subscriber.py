"""
MQTT Subscriber - Reçoit et affiche les messages du capteur
Simule le rôle d'AWS IoT Core pour la réception de données
"""

import json
from datetime import datetime
import paho.mqtt.client as mqtt  # type: ignore

# Configuration HiveMQ Cloud (doit correspondre au capteur)
MQTT_BROKER = "7be661ae342e41e28bb30488c56a0cfe.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "sensor_user"
MQTT_PASSWORD = "bY.5Gdir4iSrwWy"
TOPIC_TELEMETRY = "sensors/temperature/data"
TOPIC_COMMAND = "sensors/temperature/command"


class IoTSubscriber:
    """Simule le cloud IoT qui reçoit les données"""
    
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="iot_cloud_simulator")
        
        # Configuration pour HiveMQ Cloud (authentification + TLS)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.tls_set()  # Active TLS/SSL
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_count = 0
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback de connexion"""
        if rc == 0:
            print(f"[{datetime.now()}] ✓ Connecté au broker MQTT")
            print(f"[{datetime.now()}] ✓ En écoute sur: {TOPIC_TELEMETRY}")
            client.subscribe(TOPIC_TELEMETRY)
        else:
            print(f"[{datetime.now()}] ❌ Échec connexion: Code {rc}")
    
    def on_message(self, client, userdata, message):
        """Callback de réception de message"""
        self.message_count += 1
        
        try:
            payload = json.loads(message.payload.decode('utf-8'))
            
            print(f"\n{'='*70}")
            print(f"📨 Message #{self.message_count} reçu à {datetime.now()}")
            print(f"{'='*70}")
            print(f"🆔 Device ID:    {payload.get('device_id')}")
            print(f"🌡️  Température:  {payload.get('temperature')}°C")
            print(f"💧 Humidité:     {payload.get('humidity')}%")
            print(f"🔋 Batterie:     {payload.get('battery')}%")
            print(f"📡 Signal:       {payload.get('signal_strength')} dBm")
            print(f"⚡ Statut:       {payload.get('status')}")
            print(f"🕐 Timestamp:    {payload.get('timestamp')}")
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"❌ Erreur décodage: {e}")
    
    def send_command(self, action, value=None):
        """Envoie une commande au capteur"""
        command = {"action": action}
        if value is not None:
            command["value"] = value
        
        message = json.dumps(command)
        self.client.publish(TOPIC_COMMAND, message)
        print(f"\n🚀 Commande envoyée: {command}")
    
    def run(self):
        """Démarre la réception de messages"""
        try:
            print("="*70)
            print("☁️  CLOUD IoT SIMULATOR - Réception des messages")
            print("="*70)
            print(f"\nBroker: {MQTT_BROKER}:{MQTT_PORT}")
            print(f"Topic:  {TOPIC_TELEMETRY}")
            print("\nCommandes disponibles (tapez pendant l'exécution):")
            print("  i10 - Changer intervalle à 10 secondes")
            print("  i5  - Changer intervalle à 5 secondes")
            print("  r   - Redémarrer le capteur")
            print("  s   - Arrêter le capteur")
            print("  q   - Quitter\n")
            print("="*70)
            
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Boucle interactive
            while True:
                cmd = input("\n> ").strip().lower()
                
                if cmd.startswith('i'):
                    try:
                        interval = int(cmd[1:])
                        self.send_command("set_interval", interval)
                    except:
                        print("❌ Format: i<nombre> (ex: i10)")
                        
                elif cmd == 'r':
                    self.send_command("reboot")
                    
                elif cmd == 's':
                    self.send_command("shutdown")
                    
                elif cmd == 'q':
                    print("👋 Au revoir!")
                    break
                    
                else:
                    print("❌ Commande inconnue")
                    
        except KeyboardInterrupt:
            print("\n👋 Arrêt demandé")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            print("\n💡 SOLUTION: Vérifiez que Mosquitto est démarré")
            print("   Windows: net start mosquitto")
            print("   Linux: sudo systemctl start mosquitto")
            print("   Ou utilisez un broker public dans le code:")
            print("   MQTT_BROKER = 'test.mosquitto.org'")
        finally:
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    subscriber = IoTSubscriber()
    subscriber.run()