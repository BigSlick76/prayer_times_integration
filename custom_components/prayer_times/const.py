DOMAIN = "prayer_times"
"""Constants for the Islamic Prayer component."""
NAME = "Oissel Prayer Times"
PRAYER_TIMES_ICON = "mdi:calendar-clock"
PRAYER_JUMUA_ICON = "mdi:MosqueOutline"
PRAYER_IQAMA_ICON = "mdi:StarCrescent"
SENSOR_TYPES = {
    "Fajr": "Adhan",
    "Shurouq": "Time",
    "Sunrise": "Time",
    "Dhuhr": "Adhan",
    "Asr": "Adhan",
    "Maghrib": "Adhan",
    "Isha": "Adhan",
    "Jumua": "Adhan",
    "Jumua 2": "Adhan",
    "next_mawaqit": "time",
    "Fajr Iqama": "",  
    "Dhuhr Iqama": "",   
    "Asr Iqama": "",    
    "Maghrib Iqama": "",  
    "Isha Iqama": "",
    "Next Salat Time": "",
    "Next Salat Name": "",
    "Next Salat Preparation": "",
    "Mosque_label": "",
    "Mosque_localisation": "",
    "Mosque_url": "",
    "Mosque_image": "",
}
        
CONF_CALC_METHOD = "calculation_method"

CALC_METHODS = ["nearest", "farest"]
DEFAULT_CALC_METHOD = "nearest"

DATA_UPDATED = "Mawaqit_prayer_data_updated"

UPDATE_TIME = (1, 0, 0)

CONF_SERVER = "server"

USERNAME = "user"

PASSWORD = "password"

API = "api"
CONF_UUID ="uuid"
