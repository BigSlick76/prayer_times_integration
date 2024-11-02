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
BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")  # Fixed path issue
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
        self._state = None

    @property
    def name(self):
        return f"{self.city}_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        month = datetime.now().month
        self.time = read_daily_prayer_times(self.city, month)
        today = datetime.now().strftime('%m-%d')
        self._state = self.time.get(today, {}).get(self.prayer)

class IqamaTimeSensor(Entity):
    def __init__(self, city, prayer, iqama_delay):
        self.city = city
        self.prayer = prayer
        self.iqama_delay = iqama_delay
        self._state = None

    @property
    def name(self):
        return f"{self.city}_iqama_{self.prayer}"

    @property
    def state(self):
        return self._state

    def update(self):
        month = datetime.now().month
        base_time = read_daily_prayer_times(self.city, month)
        today = datetime.now().strftime('%m-%d')
        prayer_time = base_time.get(today, {}).get(self.prayer)
        if prayer_time:
            prayer_time_dt = datetime.strptime(prayer_time, '%H:%M')
            iqama_time = prayer_time_dt + timedelta(minutes=int(self.iqama_delay.get(self.prayer, 0)))
            self._state = iqama_time.strftime('%H:%M')

class FridayPrayerSensor(Entity):
    def __init__(self, city):
        self.city = city
        self._state = None

    @property
    def name(self):
        return f"{self.city}_friday_prayer"

    @property
    def state(self):
        return self._state

    def update(self):
        self._state = read_friday_prayer_time(self.city)

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
        prayer_times = read_daily_prayer_times(self.city, month)
        today = datetime.now().strftime('%m-%d')
        prayer_time = prayer_times.get(today, {}).get(self.prayer)

        if prayer_time:
            today_date = datetime.now().date()
            prayer_time_dt = datetime.strptime(prayer_time, '%H:%M').replace(year=today_date.year, month=today_date.month, day=today_date.day)
            self._state = int(prayer_time_dt.timestamp())
        else:
            self._state = None  # Handle case where prayer time is not found

async def update_sensors(sensors):
    for sensor in sensors:
        if hasattr(sensor, "update"):
            sensor.update()

async def async_setup(hass: HomeAssistant, config: dict):
    _LOGGER.debug("Initialisation de l'intégration Prayer Times.")
    await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    return True

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Configuration de la plateforme de capteurs pour Prayer Times.")
    cities = [name for name in os.listdir(BASE_DATA_PATH) if os.path.isdir(os.path.join(BASE_DATA_PATH, name))]
    
    sensors = []

    for city in cities:
        iqama_times = read_iqama_times(city)

        if not iqama_times:
            _LOGGER.error("Les données d'iqama sont manquantes pour la ville : %s", city)
            continue

        for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha', 'Shurouq']:
            prayer_sensor = PrayerTimeSensor(city, prayer)
            timestamp_sensor = PrayerTimeTimestampSensor(city, prayer)
            sensors.append(prayer_sensor)
            sensors.append(timestamp_sensor)
        
        friday_sensor = FridayPrayerSensor(city)
        sensors.append(friday_sensor)

    if sensors:
        add_entities(sensors)
        hass.data.setdefault(DOMAIN, {})["sensors"] = sensors
        _LOGGER.debug("Capteurs ajoutés : %s", [sensor.name for sensor in sensors])
        
        async_track_time_interval(
            hass, 
            lambda _: asyncio.run_coroutine_threadsafe(update_sensors(sensors), hass.loop),
            timedelta(seconds=10)
        )
    else:
        _LOGGER.warning("Aucun capteur créé.")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_setup_platforms(entry, ["sensor"])
    return True
