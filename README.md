# prayer_times_integration
prayer_times_integration

# Prayer Times Integration

Une intégration pour Home Assistant qui fournit les horaires de prière pour différentes villes.

## Installation

1. Clonez ce dépôt dans votre répertoire `custom_components` :
   ```bash
   git clone https://github.com/USERNAME/prayer_times_integration.git

## Structure 
custom_components/
└── prayer_times/
    ├── __init__.py
    ├── manifest.json
    ├── sensor.py
    ├── data/
    │   ├── <city_name>/
    │   │   ├── 01.csv
    │   │   ├── 02.csv
    │   │   ├── 03.csv
    │   │   ├── 04.csv
    │   │   ├── 05.csv
    │   │   ├── 06.csv
    │   │   ├── 07.csv
    │   │   ├── 08.csv
    │   │   ├── 09.csv
    │   │   ├── 10.csv
    │   │   ├── 11.csv
    │   │   ├── 12.csv
    │   │   ├── iqama.csv
    │   │   └── vendredi.csv
    └── README.md


{
  "domain": "prayer_times",
  "name": "Prayer Times",
  "documentation": "https://github.comBigSlick76/prayer_times_integration",
  "requirements": [],
  "dependencies": [],
  "codeowners": ["@BigSlick76"],
  "version": "1.0.0"
}
![Logo](http://francky.me/images/quora001.png)
