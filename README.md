# Codearch 3D Viewer Hub

An elegant, lightweight, self-hosted web platform designed for architects, designers, and real estate developers to share 3D models with clients and collaborate using interactive pin-based comments in a pure white-labeled space.

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?style=flat-square&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/codearch)

*Read this in other languages: [Polski (PL)](#polski-pl)*

---

## Key Features

- 🌐 **Interactive 3D Viewport**: Load and inspect `.glb` and `.gltf` files with optimized lighting and shadows directly in the browser (powered by Three.js).
- 💬 **Collaboration Workspace**: Place pins directly onto the 3D model geometry to create comment threads. Supports roles (Architect vs. Client) and hierarchical replies.
- 🎨 **White-Label Customization**: Change the platform name, logo, favicon, and brand colors (primary & accent) directly from the settings panel.
- 👁️ **Visual View Modes**:
  - **Conceptual (Clay)**: Matte clay material on a clean white background to inspect geometry and shadow patterns.
  - **Materials**: Render original CAD colors, textures, and environmental reflections.
  - **X-Ray (Rentgen)**: Semitransparent view in your brand color to look inside floors, ceilings, and structural components.
- 🔒 **Model Password Protection**: Lock sensitive CAD designs behind custom access passwords before sharing links or embedding them.
- 📱 **Mobile & Embed Optimized**: Fully responsive layout. Embedded `iframe` supports watermarks, privacy policies, and clean modal chat overlays on small touchscreens.
- 🗺️ **Bilingual**: Fully localized into English and Polish.

---

## Technical Stack

- **Backend**: FastAPI (Python), Uvicorn, Jinja2 Templates, SQLite.
- **Frontend**: Vanilla HTML5, CSS3 Variables, ES Modules, Three.js (no heavy build framework needed!).
- **Containerization**: Docker, Docker Compose.

---

## Quick Start (Docker)

The fastest way to deploy the 3D Viewer Hub is using Docker:

1. Create a `docker-compose.yml` file:
   ```yaml
   version: '3.8'
   services:
     3d-viewer:
       image: ghcr.io/your-username/3d-viewer:latest  # Or build locally
       build: .
       ports:
         - "8000:8000"
       environment:
         - ADMIN_PASSWORD=ChangeMeSecurity2026!
       volumes:
         - 3d-viewer-data:/app/data
       restart: always

   volumes:
     3d-viewer-data:
   ```

2. Run the command:
   ```bash
   docker compose up -d
   ```

3. Open your browser and navigate to `http://localhost:8000`. Login with the `ADMIN_PASSWORD` you configured.

---

## Local Development Setup

To run the application locally without Docker:

1. Clone the repository and navigate to the project directory.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your administrator password:
   ```bash
   cp .env.example .env
   ```
4. Run the development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
5. Open `http://localhost:8000` in your browser.

---

# Polski (PL)

Elegancka, lekka, hostowana samodzielnie platforma internetowa stworzona dla architektów, projektantów i deweloperów w celu udostępniania modeli 3D klientom i współpracy przy użyciu interaktywnych komentarzy (pinów) w przestrzeni o własnym brandingu (white-label).

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Wesprzyj-yellow.svg?style=flat-square&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/codearch)

---

## Główne Funkcje

- 🌐 **Interaktywny widok 3D**: Wczytywanie i przeglądanie plików `.glb` i `.gltf` ze zoptymalizowanym oświetleniem i cieniami bezpośrednio w przeglądarce (oparte na Three.js).
- 💬 **Współpraca i uwagi**: Nanoszenie pinezek (pinów) bezpośrednio na geometrię modelu w celu tworzenia wątków dyskusyjnych. Obsługuje role (Architekt vs. Inwestor) i odpowiedzi.
- 🎨 **Personalizacja (White-Label)**: Możliwość zmiany nazwy portalu, wgrania własnego logo, favicony oraz dostosowania kolorów przewodnich bezpośrednio z panelu ustawień.
- 👁️ **Style wyświetlania**:
  - **Koncepcyjny (Clay)**: Matowy gips na czystym białym tle do analizy kompozycji przestrzennej i cieniowania.
  - **Materiały**: Prezentacja oryginalnych kolorów, tekstur i odbić środowiskowych z Rhino/BIM.
  - **Rentgen (X-Ray)**: Półprzezroczysty widok w kolorze akcentu marki, pozwalający zajrzeć pod stropy i za ściany działowe.
- 🔒 **Zabezpieczenie hasłem**: Możliwość zablokowania dostępu do wrażliwych modeli i komentarzy unikalnym hasłem.
- 📱 **Optymalizacja mobilna i Embed**: Responsywny layout, obsługa gestów dotykowych, automatyczny znak wodny i wycentrowane okna komentarzy na telefonach.
- 🗺️ **Wielojęzyczność**: Pełne tłumaczenie interfejsu na język polski i angielski.

---

## Uruchomienie za pomocą Dockera

1. Utwórz plik `docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     3d-viewer:
       build: .
       ports:
         - "8000:8000"
       environment:
         - ADMIN_PASSWORD=ZmienMnieBezpieczenstwo2026!
       volumes:
         - 3d-viewer-data:/app/data
       restart: always

   volumes:
     3d-viewer-data:
   ```

2. Uruchom kontener:
   ```bash
   docker compose up -d
   ```

3. Otwórz w przeglądarce adres `http://localhost:8000`. Zaloguj się hasłem podanym w zmiennej `ADMIN_PASSWORD`.
