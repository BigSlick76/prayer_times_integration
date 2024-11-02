import csv
import logging
import os
import asyncio
from datetime import datetime, timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery  
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity import Entity

# Définition du domaine
DOMAIN = "prayer_times"
BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "/config/custom_components/prayer_times/data/")
_LOGGER = logging.getLogger(__name__)

def read_daily_prayer_times(city, month):
    filename = os.path.join(BASE_DATA_PATH, city, f"{month:02}.csv")
    _LOGGER.debug("Lecture des horaires de prière depuis : %s", filename)
    prayer_times = {}
    try:
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                date = row['date']
                prayer_times[date] = {
                    'Fajr': row['Fajr'],
                    'Shurouq': row['Shurouq'],
                    'Dhuhr': row['Dhuhr'],
                    'Asr': row['Asr'],
                    'Maghrib': row['Maghrib'],
                    'Isha': row['Isha']
                }
    except FileNotFoundError:
        _LOGGER.error("Fichier non trouvé : %s", filename)
    return prayer_times

def read_iqama_times(city):
    filename = os.path.join(BASE_DATA_PATH, city, "iqama.csv")
    _LOGGER.debug("Lecture des temps d'iqama depuis : %s", filename)
    try:
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            return next(reader)
    except FileNotFoundError:
        _LOGGER.error("Fichier non trouvé : %s", filename)
        return {}

def read_friday_prayer_time(city):
    filename = os.path.join(BASE_DATA_PATH, city, "vendredi.csv")
    _LOGGER.debug("Lecture de la prière du vendredi depuis : %s", filename)
    try:
        with open(filename, 'r') as file:
            return file.readline().strip()
    except FileNotFoundError:
        _LOGGER.error("Fichier non trouvé : %s", filename)
        return None

class PrayerTimeSensor(Entity):
    def __init__(self, city, prayer):
        self.city = city
        self.prayer = prayer
        self.time = None
        self._state = None

    @property
    def name(self):
        return f"{self.city}_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        month = datetime.now().month
        self.time = read_daily_prayer_times(self.city, month)  # Recharger les horaires
        today = datetime.now().strftime('%m-%d')
        self._state = self.time.get(today, {}).get(self.prayer)

class IqamaTimeSensor(Entity):
    def __init__(self, city, prayer, iqama_delay):
        self.city = city
        self.prayer = prayer
        self.iqama_delay = iqama_delay
        self._state = None
        self.base_time = None

    @property
    def name(self):
        return f"{self.city}_iqama_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        month = datetime.now().month
        self.base_time = read_daily_prayer_times(self.city, month)  # Recharger les horaires
        today = datetime.now().strftime('%m-%d')
        prayer_time = self.base_time.get(today, {}).get(self.prayer)
        if prayer_time:
            prayer_time_dt = datetime.strptime(prayer_time, '%H:%M')
            iqama_time = prayer_time_dt + timedelta(minutes=int(self.iqama_delay[self.prayer]))
            self._state = iqama_time.strftime('%H:%M')

class FridayPrayerSensor(Entity):
    def __init__(self, city):
        self.city = city
        self._state = None
        self.friday_time = None

    @property
    def name(self):
        return f"{self.city}_friday_prayer"

    @property
    def state(self):
        return self._state

    def update(self):
        month = datetime.now().month
        self.friday_time = read_friday_prayer_time(self.city)  # Recharger le temps de prière du vendredi
        self._state = self.friday_time

class PrayerTimeTimestampSensor(Entity):
    def __init__(self, city, prayer):
        self.city = city
        self.prayer = prayer
        self._state = None

    @property
    def name(self):
        return f"{self.city}_timestamp_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        month = datetime.now().month
        prayer_times = read_daily_prayer_times(self.city, month)  # Recharger les horaires
        today = datetime.now().strftime('%m-%d')
        prayer_time = prayer_times.get(today, {}).get(self.prayer)

        if prayer_time:
            # Récupérer la date d'aujourd'hui
            today_date = datetime.now().date()
            # Créer un objet datetime pour l'heure de prière
            prayer_time_dt = datetime.strptime(prayer_time, '%H:%M').replace(year=today_date.year, month=today_date.month, day=today_date.day)
            # Convertir en timestamp Unix
            timestamp = int(prayer_time_dt.timestamp())
            self._state = timestamp

async def update_sensors(sensors):
    """Met à jour tous les capteurs."""
    for sensor in sensors:
        if hasattr(sensor, "update"):
            sensor.update()

async def async_setup(hass: HomeAssistant, config: dict):
    """Configurer le domaine au chargement."""
    _LOGGER.debug("Initialisation de l'intégration Prayer Times.")
    
    # Charge la plateforme de capteurs de manière asynchrone
    await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    
    return True

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Configuration de la plateforme de capteurs pour Prayer Times.")
    cities = [name for name in os.listdir(BASE_DATA_PATH) if os.path.isdir(os.path.join(BASE_DATA_PATH, name))]
    
    sensors = []

    for city in cities:
        # Lecture des horaires et de l'iqama
        iqama_times = read_iqama_times(city)

        if not iqama_times:
            _LOGGER.error("Les données d'iqama sont manquantes pour la ville : %s", city)
            continue

        # Créer des capteurs pour les prières
        for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            prayer_sensor = PrayerTimeSensor(city, prayer)
            iqama_sensor = IqamaTimeSensor(city, prayer, iqama_times)
            timestamp_sensor = PrayerTimeTimestampSensor(city, prayer)  # Nouveau capteur pour le timestamp
            sensors.append(prayer_sensor)
            sensors.append(iqama_sensor)
            sensors.append(timestamp_sensor)  # Ajoute le capteur timestamp
        for prayer in ['Shurouq']:
            prayer_sensor = PrayerTimeSensor(city, prayer)
            #iqama_sensor = IqamaTimeSensor(city, prayer, iqama_times)
            timestamp_sensor = PrayerTimeTimestampSensor(city, prayer)  # Nouveau capteur pour le timestamp
            sensors.append(prayer_sensor)
            #sensors.append(iqama_sensor)
            sensors.append(timestamp_sensor)  # Ajoute le capteur timestamp
        # Capteur pour la prière du vendredi
        friday_sensor = FridayPrayerSensor(city)
        sensors.append(friday_sensor)

    if sensors:
        add_entities(sensors)
        hass.data.setdefault(DOMAIN, {})["sensors"] = sensors  # Stocker les capteurs
        _LOGGER.debug("Capteurs ajoutés : %s", [sensor.name for sensor in sensors])
        
        # Mise à jour des capteurs toutes les 10 secondes
        async_track_time_interval(
            hass, 
            lambda _: asyncio.run_coroutine_threadsafe(update_sensors(sensors), hass.loop),  # Exécuter la coroutine de manière sûre
            timedelta(seconds=10)
        )
    else:
        _LOGGER.warning("Aucun capteur créé.")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configurer la plateforme via Config Flow si utilisé dans le futur."""
    await hass.config_entries.async_setup_platforms(entry, ["sensor"])
    await hass.config_entries.async_setup_platforms(entry, ["date_time"])
    return True
