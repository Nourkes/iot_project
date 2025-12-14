Simulation IoT Complète 

Ce projet permet de simuler une architecture IoT complète (Capteur → Broker → Dashboard) 

📌 Architecture

Capteur Virtuel (virtual_sensor.py)
Simule un appareil IoT qui envoie des données (Température, Humidité) et écoute des commandes.

Dashboard (dashboard_streamlit.py)
Interface Web pour visualiser les données en temps réel et contrôler le capteur.

Broker MQTT
Utilise le broker public test.mosquitto.org pour relier le capteur et le dashboard.

✅ Prérequis

Python 3.x installé

🔧 Installation

Installez les bibliothèques nécessaires avec :

pip install -r requirements.txt

🚀 Lancement de la Démo

Il faut lancer deux terminaux séparés (ou deux fenêtres de commande).

🖥️ Terminal 1 : Le Capteur

Lancez le script du capteur. Il commencera à envoyer des données :

python virtual_sensor.py

🌐 Terminal 2 : Le Dashboard

Lancez le dashboard avec Streamlit :

streamlit run dashboard_streamlit.py


Cela ouvrira automatiquement une page web (généralement http://localhost:8501) où :

vous verrez les graphiques se mettre à jour en temps réel

vous pourrez envoyer des commandes (changer l’intervalle, redémarrer, etc.)

🧭 Commandes Disponibles

Depuis le Dashboard, vous pouvez :

Changer la fréquence d’envoi des données

Simuler un redémarrage du capteur

Arrêter le capteur à distance

Toutes les actions sont visibles dans le Terminal 1 (logs du capteur).