import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery  

_LOGGER = logging.getLogger(__name__)

DOMAIN = "prayer_times"

async def async_setup(hass: HomeAssistant, config: dict):
    """Configurer le domaine au chargement."""
    _LOGGER.debug("Initialisation de l'intégration Prayer Times.")
    
    # Charge la plateforme de capteurs de manière asynchrone
    await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configurer la plateforme via Config Flow si utilisé dans le futur."""
    await hass.config_entries.async_setup_platforms(entry, ["sensor"])
    return True
