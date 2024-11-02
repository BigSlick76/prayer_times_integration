import csv
import logging
from datetime import datetime, timedelta
import os
from homeassistant.helpers.entity import Entity

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

class FridayPrayerSensor(Entity):
    def __init__(self, city, friday_time):
        self.city = city
        self.friday_time = friday_time
        self._state = friday_time

    @property
    def name(self):
        return f"{self.city}_friday_prayer"

    @property
    def state(self):
        return self._state

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

        # Créer des capteurs pour les prières
        for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            sensors.append(PrayerTimeSensor(city, prayer, prayer_times))
            sensors.append(IqamaTimeSensor(city, prayer, prayer_times, iqama_times))

        # Capteur pour la prière du vendredi
        if friday_time:
            sensors.append(FridayPrayerSensor(city, friday_time))

    if sensors:
        add_entities(sensors)
        _LOGGER.debug("Capteurs ajoutés : %s", [sensor.name for sensor in sensors])
    else:
        _LOGGER.warning("Aucun capteur créé.")
