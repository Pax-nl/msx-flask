# MSX Flask Directory Server

Een kleine Flask-applicatie die een directorylisting serveert vanuit de `files/` map. Deze repository is bedoeld om de inhoud van een MSX-bestandenmap via HTTP beschikbaar te maken, met focus op ROM- en DSK-bestanden.

## Inhoud

- `flask_directory_server.py` - Flask-applicatie die `files/` indexeert en lijstresultaten retourneert.
- `Dockerfile` - Docker image voor productie, met `gunicorn` als WSGI-server.
- `docker-compose.yml` - Lokale ontwikkelomgeving met gemounte `files/` map.
- `requirements.txt` - Python dependencies.
- `.dockerignore` - Bouwcontext uitsluiten voor grote bestanden en gevoelige gegevens.
- `.gitignore` - Git negeert grote assets en lokale configuratie.
- `flask_directory_server.py` - bevat nu een beheerdersinterface op `/manage` voor upload, delete, hernoemen, verplaatsen en mappen aanmaken.

## Vereisten

- Docker
- Docker Compose (of `docker compose` ondersteund door je Docker-versie)

## Lokale ontwikkeling

1. Bouw en start de service:

```bash
docker compose up --build
```

2. Open de service in je browser of een client:

```text
http://localhost
```

3. Stop de service met:

```bash
docker compose down
```

## Docker build en run

Bouw de image:

```bash
docker build -t msx-flask .
```

Start de container met een gekoppelde `files/` map en maak de service bereikbaar op hostpoort 80:

```bash
docker run -p 80:5001 -v $(pwd)/files:/app/files:ro --env-file .env msx-flask
```

> Gebruik `:ro` als je de bestanden alleen wil lezen vanuit de container.

## Environment variables

De app luistert altijd intern op port `5001`; die interne poort is niet configureerbaar.

Je kunt `.env` gebruiken om de externe hostpoort te configureren voor Docker Compose of een proxy zoals nginx.

Voorbeeldbestand:

```env
HOST_PORT=80
DEBUG=0
FLASK_ENV=production
```

- `HOST_PORT=80` bepaalt welke hostpoort naar containerpoort `5001` wordt geleid.
- `DEBUG=1` kan worden gebruikt voor extra logging tijdens lokale testen.
- `FLASK_ENV=production` is de aanbevolen waarde voor productie.

## Bestanden en assets

- Voeg geen grote `*.dsk` of `*.DSK` bestanden aan Git toe.
- De `files/` map is gemarkeerd in `.dockerignore` zodat deze niet onnodig in de Docker buildcontext komt.

## Opmerkingen

- Deze setup gebruikt `gunicorn` als productie-server in plaats van de Flask debug-server.
- De `files/` map wordt idealiter via een volume gemount, zodat de container licht blijft.
