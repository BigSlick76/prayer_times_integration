import csv
import logging
import os
from datetime import datetime, timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery  
from homeassistant.helpers.event import async_track_time_interval  # Importation nécessaire
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
    def __init__(self, city, prayer, time):
        self.city = city
        self.prayer = prayer
        self.time = time
        self._state = None

    @property
    def name(self):
        return f"{self.city}_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        today = datetime.now().strftime('%m-%d')
        self._state = self.time.get(today, {}).get(self.prayer)
    
    @property
    def icon(self):
        """Icon to display in the front end."""
        return "mdi:mosque-outline"

class IqamaTimeSensor(Entity):
    def __init__(self, city, prayer, base_time, iqama_delay):
        self.city = city
        self.prayer = prayer
        self.base_time = base_time
        self.iqama_delay = iqama_delay
        self._state = None

    @property
    def name(self):
        return f"{self.city}_iqama_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        today = datetime.now().strftime('%m-%d')
        prayer_time = self.base_time.get(today, {}).get(self.prayer)
        if prayer_time:
            prayer_time_dt = datetime.strptime(prayer_time, '%H:%M')
            iqama_time = prayer_time_dt + timedelta(minutes=int(self.iqama_delay[self.prayer]))
            self._state = iqama_time.strftime('%H:%M')
    
    @property
    def icon(self):
        """Icon to display in the front end."""
        return "mdi:calendar-clock"

class FridayPrayerSensor(Entity):
    def __init__(self, city):
        self.city = city
        self._state = None
        self.friday_time = None

    @property
    def name(self):
        return f"{self.city}_friday_prayer"

    @property
    def unique_id(self):
        """Identifiant unique pour cette entité."""
        return f"{self.city}_friday_prayer"

    @property
    def state(self):
        return self._state

    def update(self):
        self.friday_time = read_friday_prayer_time(self.city)
        self._state = self.friday_time

    @property
    def icon(self):
        """Icon to display in the front end."""
        return "mdi:mosque"

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
    
    # Initialiser les capteurs
    sensors = hass.data.get(DOMAIN, {}).get("sensors", [])
    
    # Mise à jour des capteurs toutes les 10 secondes
    async_track_time_interval(
        hass, 
        lambda _: update_sensors(sensors), 
        timedelta(seconds=10)
    )
    
    return True

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Configuration de la plateforme de capteurs pour Prayer Times.")
    cities = [name for name in os.listdir(BASE_DATA_PATH) if os.path.isdir(os.path.join(BASE_DATA_PATH, name))]
    month = datetime.now().month

    sensors = []

    for city in cities:
        prayer_times = read_daily_prayer_times(city, month)
        iqama_times = read_iqama_times(city)
        friday_time = read_friday_prayer_time(city)

        if not prayer_times or not iqama_times:
            _LOGGER.error("Les données de prière ou d'iqama sont manquantes pour la ville : %s", city)
            continue

        for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            prayer_sensor = PrayerTimeSensor(city, prayer, prayer_times)
            iqama_sensor = IqamaTimeSensor(city, prayer, prayer_times, iqama_times)
            sensors.append(prayer_sensor)
            sensors.append(iqama_sensor)

        if friday_time:
            sensors.append(FridayPrayerSensor(city))

    if sensors:
        add_entities(sensors)
        hass.data.setdefault(DOMAIN, {})["sensors"] = sensors  # Stocker les capteurs
        _LOGGER.debug("Capteurs ajoutés : %s", [sensor.name for sensor in sensors])
    else:
        _LOGGER.warning("Aucun capteur créé.")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configurer la plateforme via Config Flow si utilisé dans le futur."""
    await hass.config_entries.async_setup_platforms(entry, ["sensor"])
    return True
    