"""
Dashboard IoT en Python avec Streamlit
Affiche en temps réel les données envoyées par le capteur virtuel.
Broker : HiveMQ Cloud
Topic : sensors/temperature/data (télémétrie)
"""
import json
import time
from datetime import datetime
from collections import deque
from queue import Queue
import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd

# ==== CONFIG MQTT HiveMQ Cloud ====
MQTT_BROKER = "7be661ae342e41e28bb30488c56a0cfe.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "sensor_user"
MQTT_PASSWORD = "bY.5Gdir4iSrwWy"
TOPIC_TELEMETRY = "sensors/temperature/data"

# Taille de l'historique pour les graphes
MAX_POINTS = 100

# ==== QUEUE GLOBALE (partagée entre threads) ====
# On la crée en dehors de session_state pour éviter les problèmes de threading
if "global_queue" not in st.session_state:
    st.session_state.global_queue = Queue()

# ==== ÉTAT PERSISTANT (survivre aux rerun) ====
if "data_history" not in st.session_state:
    st.session_state.data_history = deque(maxlen=MAX_POINTS)

if "last_payload" not in st.session_state:
    st.session_state.last_payload = None

if "connection_status" not in st.session_state:
    st.session_state.connection_status = "Déconnecté"

# ==== CALLBACKS MQTT (thread séparé) ====
def on_connect(client, userdata, flags, rc):
    """Callback appelé lors de la connexion"""
    if rc == 0:
        print(f"[{datetime.now()}] ✓ Connecté au broker, abonnement à {TOPIC_TELEMETRY}")
        client.subscribe(TOPIC_TELEMETRY)
        # On ne peut pas modifier session_state ici, on utilisera un indicateur
    else:
        print(f"❌ Erreur de connexion MQTT: {rc}")

def on_message(client, userdata, msg):
    """
    Callback appelé lors de la réception d'un message.
    IMPORTANT : On utilise userdata (la queue) au lieu de st.session_state
    """
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        # On pousse le payload dans la queue passée via userdata
        userdata.put(payload)
        print(f"[{datetime.now()}] 📥 Message reçu: Temp={payload['temperature']}°C")
    except Exception as e:
        print(f"❌ Erreur de décodage : {e}")

# ==== INITIALISATION MQTT (UNE SEULE FOIS) ====
if "mqtt_client" not in st.session_state:
    # Créer le client MQTT avec la queue comme userdata
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1,
        client_id="streamlit_dashboard",
        userdata=st.session_state.global_queue  # Passer la queue ici
    )
    
    # Configuration pour HiveMQ Cloud (authentification + TLS)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set()  # Active TLS/SSL
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()  # thread MQTT en arrière-plan
        st.session_state.mqtt_client = client
        st.session_state.connection_status = "Connecté"
        print(f"[{datetime.now()}] 🚀 Client MQTT démarré")
    except Exception as e:
        st.session_state.connection_status = f"Erreur: {e}"
        print(f"❌ Erreur connexion MQTT: {e}")

# ==== CONSOMMER LES MESSAGES DE LA QUEUE ====
# Ici on est dans le thread Streamlit, on peut utiliser session_state
message_count = 0
while not st.session_state.global_queue.empty():
    try:
        payload = st.session_state.global_queue.get_nowait()
        st.session_state.last_payload = payload
        
        # Ajouter à l'historique
        st.session_state.data_history.append({
            "time": datetime.fromisoformat(payload["timestamp"]),
            "temperature": payload["temperature"],
            "humidity": payload["humidity"],
            "battery": payload["battery"]
        })
        message_count += 1
    except:
        break

# ==== UI STREAMLIT ====
st.set_page_config(page_title="IoT Dashboard", layout="wide", page_icon="📊")

st.title("📊 Dashboard IoT ")

# Barre d'info avec statut de connexion
status_color = "🟢" if st.session_state.connection_status == "Connecté" else "🔴"
st.markdown(
    f"""
*Broker* : {MQTT_BROKER}:{MQTT_PORT}  
*Topic télémétrie* : {TOPIC_TELEMETRY}  
*Statut* : {status_color} {st.session_state.connection_status}  
*Messages reçus* : {len(st.session_state.data_history)}
"""
)

if st.session_state.connection_status != "Connecté":
    st.warning("⚠ Non connecté au broker MQTT. Vérifie que virtual_sensor.py est lancé.")

st.markdown("---")

# ==== MÉTRIQUES EN TEMPS RÉEL ====
col1, col2, col3 = st.columns(3)

if st.session_state.last_payload is not None:
    p = st.session_state.last_payload
    
    col1.metric(
        "🌡 Température (°C)", 
        f"{p['temperature']:.2f}",
        delta=None
    )
    col2.metric(
        "💧 Humidité (%)", 
        f"{p['humidity']:.2f}",
        delta=None
    )
    col3.metric(
        "🔋 Batterie (%)", 
        f"{p['battery']}",
        delta=None
    )
    
    # Informations supplémentaires
    with st.expander("ℹ Détails du dernier message"):
        st.json(p)
else:
    col1.metric("🌡 Température (°C)", "—")
    col2.metric("💧 Humidité (%)", "—")
    col3.metric("🔋 Batterie (%)", "—")

st.markdown("---")

# ==== GRAPHES ====
if len(st.session_state.data_history) > 0:
    df = pd.DataFrame(list(st.session_state.data_history))
    df = df.set_index("time")
    
    tab1, tab2, tab3 = st.tabs(["📈 Température", "💧 Humidité", "🔋 Batterie"])
    
    with tab1:
        st.line_chart(df["temperature"], use_container_width=True)
    
    with tab2:
        st.line_chart(df["humidity"], use_container_width=True)
    
    with tab3:
        st.line_chart(df["battery"], use_container_width=True)
    
    # Tableau des dernières valeurs
    with st.expander("📋 Historique des données"):
        st.dataframe(df.tail(20).sort_index(ascending=False), use_container_width=True)
else:
    st.info("⏳ En attente de données… Assure-toi que virtual_sensor.py est en cours d'exécution.")
    st.code("python virtual_sensor.py", language="bash")

# ==== CONTRÔLES (DOWNLINK COMMANDS) ====
st.markdown("---")
st.subheader("🎛 Commandes de contrôle (Downlink)")

col_cmd1, col_cmd2, col_cmd3 = st.columns(3)

with col_cmd1:
    st.markdown("*Intervalle d'échantillonnage*")
    interval = st.number_input("Secondes", min_value=1, max_value=60, value=5, key="interval")
    if st.button("📊 Changer l'intervalle", use_container_width=True):
        command = {"action": "set_interval", "value": interval}
        st.session_state.mqtt_client.publish(
            "sensors/temperature/command",
            json.dumps(command),
            qos=1
        )
        st.success(f"✅ Commande envoyée : intervalle = {interval}s")

with col_cmd2:
    st.markdown("*Gestion du capteur*")
    if st.button("🔄 Redémarrer", use_container_width=True):
        command = {"action": "reboot"}
        st.session_state.mqtt_client.publish(
            "sensors/temperature/command",
            json.dumps(command),
            qos=1
        )
        st.warning("⚠ Redémarrage du capteur en cours...")
    
    if st.button("🛑 Arrêter", use_container_width=True):
        command = {"action": "shutdown"}
        st.session_state.mqtt_client.publish(
            "sensors/temperature/command",
            json.dumps(command),
            qos=1
        )
        st.error("❌ Commande d'arrêt envoyée")

with col_cmd3:
    st.markdown("*Statistiques*")
    st.metric("Messages envoyés", len(st.session_state.data_history))
    if st.button("🗑 Effacer l'historique", use_container_width=True):
        st.session_state.data_history.clear()
        st.session_state.last_payload = None
        st.info("🧹 Historique effacé")

# ==== REFRESH AUTO ====
time.sleep(2)  # Attendre 2 secondes avant le prochain refresh
st.rerun()