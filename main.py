import os
import shutil
import sqlite3
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Codearch 3D Viewer Hub")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/show/") or path.startswith("/embed/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Configuration
DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "comments.db")

DEFAULT_SETTINGS = {
    "lang": "pl",
    "hub_name": "Viewer",
    "favicon_filename": "",
    "logo_filename": "",
    "primary_color": "#6366f1",
    "accent_color": "#a855f7",
    "default_view_mode": "clay",
    "default_shadows": "1",
    "default_shadows_soft": "1",
    "default_shadow_transparency": "0.15",
    "default_sun_intensity": "2.2",
    "default_ambient_intensity": "1.00",
    "default_auto_rotate": "0",
    "persona_admin": "Architekt",
    "persona_viewer": "Klient",
    "client_can_delete_own": "1",
    "client_can_edit_own": "1",
    "max_upload_size": "100",
    "buymeacoffee_url": "https://www.buymeacoffee.com/codearch"
}

translations = {
    "pl": {
        "login_title": "Logowanie | Codearch 3D Hub",
        "login_header": "Panel Logowania",
        "login_sub": "Wprowadź hasło administratora, aby zarządzać modelami 3D",
        "login_placeholder": "Hasło administratora...",
        "login_btn": "Zaloguj się",
        "login_error": "Błędne hasło",
        
        "dash_title": "Dashboard | Codearch 3D Hub",
        "dash_sub": "Udostępnianie i przeglądanie modeli 3D",
        "logout": "Wyloguj",
        "upload_title": "Przeciągnij i upuść plik modelu 3D",
        "upload_sub": "Obsługiwane formaty: .glb lub .gltf (zalecany skompresowany GLB)",
        "upload_progress": "Wgrywanie pliku:",
        "upload_success": "Model został pomyślnie przesłany!",
        "upload_err_format": "Nieprawidłowy format pliku! Wybierz .glb lub .gltf",
        "upload_err_size": "Rozmiar pliku przekracza dozwolony limit ({limit} MB)!",
        
        "your_models": "Twoje Modele 3D",
        "no_models": "Brak wgranych modeli",
        "no_models_sub": "Przeciągnij swój pierwszy model do strefy przesyłania powyżej.",
        "open_model": "Otwórz",
        "copy_link": "Kopiuj Link",
        "copy_iframe": "Kod Iframe",
        "comments": "Komentarze",
        "delete_model": "Usuń Model",
        "confirm_delete_model": "Czy na pewno chcesz trwale usunąć ten model?",
        "toast_copied_link": "Skopiowano link do udostępnienia!",
        "toast_copied_iframe": "Skopiowano kod do osadzenia!",
        "toast_comments_on": "Włączono komentarze dla modelu!",
        "toast_comments_off": "Wyłączono komentarze dla modelu!",
        "toast_comments_err": "Nie udało się zmienić ustawień komentarzy.",
        "dash_password": "Hasło",
        "dash_password_placeholder": "Wpisz hasło...",
        
        "settings_btn": "Ustawienia",
        "settings_title": "Ustawienia Systemowe",
        "save_settings_btn": "Zapisz Ustawienia",
        
        "viewer_clay": "Koncepcyjny",
        "viewer_materials": "Materiały",
        "viewer_xray": "Rentgen",
        "viewer_loading": "Wczytywanie modelu 3D...",
        "viewer_controls_left": "Lewy przycisk: Obracanie kamery",
        "viewer_controls_right": "Prawy przycisk / Shift + Lewy: Przesunięcie",
        "viewer_controls_wheel": "Rolka myszy: Zbliżenie",
        "viewer_layer_structure": "Struktura modelu",
        "viewer_elements": "Elementy Modelu",
        "viewer_no_layers": "Brak zdefiniowanych warstw.",
        "viewer_loading_structure": "Wczytywanie struktury...",
        "viewer_display_options": "Opcje wyświetlania",
        "viewer_bg_color": "Kolor Tła",
        "viewer_sun_pos": "Pozycja Słońca",
        "viewer_sun_azimuth": "Azymut (Kierunek)",
        "viewer_sun_elevation": "Elewacja (Wysokość)",
        "viewer_shadows": "Cienie Rzucane",
        "viewer_shadows_toggle": "Ostre cienie brył",
        "viewer_shadows_soft": "Miękkie krawędzie cieni",
        "viewer_shadows_transparency": "Przezroczystość cieni",
        "viewer_lighting": "Oświetlenie",
        "viewer_sun_intensity": "Natężenie słońca",
        "viewer_ambient_light": "Światło otoczenia",
        "viewer_camera_view": "Kamera i Widok",
        "viewer_auto_rotate": "Obracaj automatycznie",
        "viewer_grid": "Siatka pomocnicza (Grid)",
        "viewer_center_view": "Centruj widok",
        
        "comm_title": "Tryb Komentarzy",
        "comm_add_btn": "Dodaj Komentarz",
        "comm_list_title": "Lista Komentarzy",
        "comm_empty": "Brak komentarzy. Kliknij \"Dodaj Komentarz\", aby umieścić pierwszy dymek.",
        "comm_replies_count": "odp.",
        "comm_author_placeholder": "Twoje imię...",
        "comm_text_placeholder": "Napisz komentarz...",
        "comm_save": "Zapisz",
        "comm_cancel": "Anuluj",
        "comm_delete": "Usuń",
        "comm_reply_placeholder": "Napisz odpowiedź...",
        "comm_reply_btn": "Odpowiedz",
        "comm_confirm_delete": "Czy na pewno chcesz usunąć ten komentarz?",
        "comm_confirm_delete_reply": "Czy na pewno chcesz usunąć tę odpowiedź?",
        "comm_err_author": "Nazwa autora jest wymagana",
        "comm_err_text": "Treść komentarza jest wymagana",
        "comm_err_reply": "Treść odpowiedzi jest wymagana",
        "comm_err_forbidden_edit": "Nie masz uprawnień do edycji tego wpisu",
        "comm_err_forbidden_delete": "Nie masz uprawnień do usunięcia tego wpisu",
        
        "admin_settings_success": "Ustawienia zostały zapisane!",
        "admin_settings_err": "Błąd podczas zapisywania ustawień.",
        
        "viewer_password_required": "Ten model jest chroniony hasłem",
        "viewer_password_placeholder": "Wpisz hasło do modelu...",
        "viewer_password_submit": "Odblokuj",
        "viewer_password_incorrect": "Nieprawidłowe hasło!",
        "footer_powered_by": "Dumnie zasilane przez <a href=\"https://www.codearch.pl\" target=\"_blank\" style=\"color: var(--accent); text-decoration: none; font-weight: 600; transition: opacity 0.2s;\" onmouseover=\"this.style.opacity='0.8'\" onmouseout=\"this.style.opacity='1'\">Codearch</a>",
        "viewer_powered_by": "zasilane przez <a href=\"https://www.codearch.pl\" target=\"_blank\">Codearch</a>",
        "privacy_policy_title": "Polityka Prywatności",
        "privacy_policy_text": "<p>Portal <strong>Codearch 3D Viewport</strong> dba o Twoją prywatność. Wykorzystujemy pliki cookies wyłącznie do celów technicznych i funkcjonalnych:</p><p>• <strong>Sesja administratora</strong>: bezpieczne logowanie panelu zarządzania.<br>• <strong>Język</strong>: zapamiętanie wybranego języka interfejsu (PL/EN).<br>• <strong>Sesja przeglądania</strong>: tymczasowe trzymanie hasła modelu w celu odblokowania zasobów.</p><p>Nie używamy plików cookies stron trzecich, analityki reklamowej ani profilowania użytkowników.</p>"
    },
    "en": {
        "login_title": "Login | Codearch 3D Hub",
        "login_header": "Admin Login",
        "login_sub": "Enter admin password to manage 3D models",
        "login_placeholder": "Admin password...",
        "login_btn": "Sign In",
        "login_error": "Incorrect password",
        
        "dash_title": "Dashboard | Codearch 3D Hub",
        "dash_sub": "Share and view 3D models",
        "logout": "Logout",
        "upload_title": "Drag and drop 3D model file",
        "upload_sub": "Supported formats: .glb or .gltf (compressed GLB recommended)",
        "upload_progress": "Uploading file:",
        "upload_success": "Model uploaded successfully!",
        "upload_err_format": "Invalid file format! Choose .glb or .gltf",
        "upload_err_size": "File size exceeds the allowed limit ({limit} MB)!",
        
        "your_models": "Your 3D Models",
        "no_models": "No models uploaded yet",
        "no_models_sub": "Drag your first model to the upload zone above.",
        "open_model": "Open",
        "copy_link": "Copy Link",
        "copy_iframe": "Iframe Code",
        "comments": "Comments",
        "delete_model": "Delete Model",
        "confirm_delete_model": "Are you sure you want to permanently delete this model?",
        "toast_copied_link": "Link copied to clipboard!",
        "toast_copied_iframe": "Iframe code copied to clipboard!",
        "toast_comments_on": "Comments enabled for the model!",
        "toast_comments_off": "Comments disabled for the model!",
        "toast_comments_err": "Failed to update comments settings.",
        "dash_password": "Password",
        "dash_password_placeholder": "Enter password...",
        
        "settings_btn": "Settings",
        "settings_title": "System Settings",
        "save_settings_btn": "Save Settings",
        
        "viewer_clay": "Conceptual",
        "viewer_materials": "Materials",
        "viewer_xray": "X-Ray",
        "viewer_loading": "Loading 3D model...",
        "viewer_controls_left": "Left click: Rotate camera",
        "viewer_controls_right": "Right click / Shift + Left: Pan camera",
        "viewer_controls_wheel": "Scroll wheel: Zoom",
        "viewer_layer_structure": "Model structure",
        "viewer_elements": "Model Elements",
        "viewer_no_layers": "No defined layers found.",
        "viewer_loading_structure": "Loading structure...",
        "viewer_display_options": "Display options",
        "viewer_bg_color": "Background Color",
        "viewer_sun_pos": "Sun Position",
        "viewer_sun_azimuth": "Azimuth (Direction)",
        "viewer_sun_elevation": "Elevation (Height)",
        "viewer_shadows": "Cast Shadows",
        "viewer_shadows_toggle": "Opaque shadows",
        "viewer_shadows_soft": "Soft shadow edges",
        "viewer_shadows_transparency": "Shadow opacity",
        "viewer_lighting": "Lighting",
        "viewer_sun_intensity": "Sun intensity",
        "viewer_ambient_light": "Ambient light",
        "viewer_camera_view": "Camera & View",
        "viewer_auto_rotate": "Auto-rotate",
        "viewer_grid": "Reference Grid",
        "viewer_center_view": "Center view",
        
        "comm_title": "Comments Mode",
        "comm_add_btn": "Add Comment",
        "comm_list_title": "Comments List",
        "comm_empty": "No comments yet. Click \"Add Comment\" to place the first pin.",
        "comm_replies_count": "replies",
        "comm_author_placeholder": "Your name...",
        "comm_text_placeholder": "Write a comment...",
        "comm_save": "Save",
        "comm_cancel": "Cancel",
        "comm_delete": "Delete",
        "comm_reply_placeholder": "Write a reply...",
        "comm_reply_btn": "Reply",
        "comm_confirm_delete": "Are you sure you want to delete this comment?",
        "comm_confirm_delete_reply": "Are you sure you want to delete this reply?",
        "comm_err_author": "Author name is required",
        "comm_err_text": "Comment content is required",
        "comm_err_reply": "Reply content is required",
        "comm_err_forbidden_edit": "You don't have permission to edit this entry",
        "comm_err_forbidden_delete": "You don't have permission to delete this entry",
        
        "admin_settings_success": "Settings saved successfully!",
        "admin_settings_err": "Error saving settings.",
        
        "viewer_password_required": "This model is password protected",
        "viewer_password_placeholder": "Enter model password...",
        "viewer_password_submit": "Unlock",
        "viewer_password_incorrect": "Incorrect password!",
        "footer_powered_by": "Proudly powered by <a href=\"https://www.codearch.pl\" target=\"_blank\" style=\"color: var(--accent); text-decoration: none; font-weight: 600; transition: opacity 0.2s;\" onmouseover=\"this.style.opacity='0.8'\" onmouseout=\"this.style.opacity='1'\">Codearch</a>",
        "viewer_powered_by": "powered by <a href=\"https://www.codearch.pl\" target=\"_blank\">Codearch</a>",
        "privacy_policy_title": "Privacy Policy",
        "privacy_policy_text": "<p>The <strong>Codearch 3D Viewport</strong> portal respects your privacy. We use browser cookies and local storage solely for technical and functional purposes:</p><p>• <strong>Admin session</strong>: for secure login to the management dashboard.<br>• <strong>Language</strong>: to remember your selected interface language (PL/EN).<br>• <strong>Viewing session</strong>: to temporarily store model access passwords to load resources.</p><p>We do not use any third-party tracking cookies, marketing pixels, or analytics.</p>"
    }
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT,
            x REAL,
            y REAL,
            z REAL,
            camera_x REAL,
            camera_y REAL,
            camera_z REAL,
            target_x REAL,
            target_y REAL,
            target_z REAL,
            text TEXT,
            author_name TEXT,
            author_type TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS model_settings (
            model_name TEXT PRIMARY KEY,
            comments_enabled INTEGER DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comment_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            author_name TEXT NOT NULL,
            author_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (comment_id) REFERENCES comments(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    for k, v in DEFAULT_SETTINGS.items():
        cur.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES (?, ?)", (k, str(v)))
        
    # Automatically update to the new ideal default lighting values if still at old defaults
    cur.execute("UPDATE global_settings SET value = '2.2' WHERE key = 'default_sun_intensity' AND value = '1.8'")
    cur.execute("UPDATE global_settings SET value = '1.00' WHERE key = 'default_ambient_intensity' AND value = '0.80'")
    cur.execute("UPDATE global_settings SET value = 'clay' WHERE key = 'default_view_mode' AND value IN ('materials', 'arctic')")
        
    try:
        cur.execute("ALTER TABLE model_settings ADD COLUMN password_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE model_settings ADD COLUMN password_value TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

init_db()

def get_all_settings() -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM global_settings")
        rows = cur.fetchall()
        conn.close()
        settings = DEFAULT_SETTINGS.copy()
        for row in rows:
            settings[row[0]] = row[1]
        return settings
    except Exception as e:
        print(f"Error fetching global settings: {e}")
        return DEFAULT_SETTINGS.copy()

def are_comments_enabled(filename: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT comments_enabled FROM model_settings WHERE model_name = ?", (filename,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            return True
        return bool(row[0])
    except Exception as e:
        print(f"Error checking comments enabled: {e}")
        return True

def get_model_settings(filename: str) -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT comments_enabled, password_enabled, password_value FROM model_settings WHERE model_name = ?", (filename,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            return {"comments_enabled": True, "password_enabled": False, "password_value": ""}
        return {
            "comments_enabled": bool(row[0]),
            "password_enabled": bool(row[1]),
            "password_value": row[2] or ""
        }
    except Exception as e:
        print(f"Error checking model settings: {e}")
        return {"comments_enabled": True, "password_enabled": False, "password_value": ""}

def check_model_password_auth(filename: str, request: Request, password: Optional[str] = None) -> bool:
    if is_authenticated(request):
        return True
    m_settings = get_model_settings(filename)
    if not m_settings["password_enabled"]:
        return True
    if not password:
        password = request.query_params.get("password")
    if not password:
        password = request.headers.get("X-Model-Password")
    return password == m_settings["password_value"]

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Setup templates
def global_settings_context(request: Request) -> dict:
    settings = get_all_settings()
    # Detect language: check parameter, then cookie, then header, then fallback to db default
    lang = request.query_params.get("lang")
    if not lang:
        lang = request.cookies.get("lang")
    
    db_default_lang = settings.get("lang", "pl")
    
    if not lang:
        accept_lang = request.headers.get("accept-language", "")
        if "en" in accept_lang.lower()[:5]:
            lang = "en"
        else:
            lang = "pl"
            
    if not request.query_params.get("lang") and not request.cookies.get("lang"):
        lang = db_default_lang

    if lang not in ("pl", "en"):
        lang = "pl"
        
    t = translations.get(lang, translations["pl"])
    
    return {
        "s": settings,
        "t": t,
        "current_lang": lang
    }

templates = Jinja2Templates(directory="templates", context_processors=[global_settings_context])

# Helper to check authentication
def is_authenticated(request: Request) -> bool:
    return request.cookies.get("session_token") == "authenticated_codearch_admin"

def require_admin(request: Request):
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )

# Public endpoints
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, error: Optional[str] = None):
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login_post(password: str = Form(...)):
    settings = get_all_settings()
    db_password = settings.get("admin_password")
    expected_password = db_password if db_password else ADMIN_PASSWORD
    
    if password == expected_password:
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="session_token",
            value="authenticated_codearch_admin",
            httponly=True,
            max_age=86400 * 30, # 30 days
            samesite="lax"
        )
        return response
    return RedirectResponse(url="/login?error=Błędne hasło", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response

# Admin dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard_get(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # List models
    files = []
    if os.path.exists(DATA_DIR):
        for name in os.listdir(DATA_DIR):
            path = os.path.join(DATA_DIR, name)
            if os.path.isfile(path) and name.lower().endswith(('.glb', '.gltf')):
                size_mb = os.path.getsize(path) / (1024 * 1024)
                m_settings = get_model_settings(name)
                files.append({
                    "name": name,
                    "size": f"{size_mb:.2f} MB",
                    "comments_enabled": m_settings["comments_enabled"],
                    "password_enabled": m_settings["password_enabled"],
                    "password_value": m_settings["password_value"]
                })
    
    return templates.TemplateResponse("index.html", {"request": request, "files": files})

@app.post("/upload")
async def upload_model(request: Request, file: UploadFile = File(...)):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    settings = get_all_settings()
    try:
        max_size_mb = float(settings.get("max_upload_size", "100"))
    except ValueError:
        max_size_mb = 100.0
        
    filename = file.filename
    if not filename.lower().endswith(('.glb', '.gltf')):
        raise HTTPException(status_code=400, detail="Niewłaściwy format pliku. Dozwolone są tylko .glb oraz .gltf")
        
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size_bytes = int(content_length)
            if size_bytes > max_size_mb * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"Plik przekracza maksymalny dozwolony limit ({max_size_mb} MB)")
        except ValueError:
            pass
            
    target_path = os.path.join(DATA_DIR, filename)
    size_counter = 0
    max_size_bytes = max_size_mb * 1024 * 1024
    
    with open(target_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024) # read 1MB chunks
            if not chunk:
                break
            size_counter += len(chunk)
            if size_counter > max_size_bytes:
                buffer.close()
                if os.path.exists(target_path):
                    os.remove(target_path)
                raise HTTPException(status_code=400, detail=f"Plik przekracza maksymalny dozwolony limit ({max_size_mb} MB)")
            buffer.write(chunk)
            
    return {"status": "success", "filename": filename}

@app.post("/api/admin/settings")
async def save_settings(
    request: Request,
    lang: str = Form(...),
    hub_name: str = Form(...),
    primary_color: str = Form(...),
    accent_color: str = Form(...),
    persona_admin: str = Form(...),
    persona_viewer: str = Form(...),
    client_can_delete_own: str = Form("0"),
    client_can_edit_own: str = Form("0"),
    default_view_mode: str = Form("clay"),
    default_shadows: str = Form("0"),
    default_shadows_soft: str = Form("0"),
    default_shadow_transparency: str = Form("0.15"),
    default_sun_intensity: str = Form("1.8"),
    default_ambient_intensity: str = Form("0.80"),
    default_auto_rotate: str = Form("0"),
    max_upload_size: str = Form("100"),
    buymeacoffee_url: str = Form(""),
    current_password: Optional[str] = Form(None),
    new_password: Optional[str] = Form(None),
    confirm_new_password: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    favicon: Optional[UploadFile] = File(None)
):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    import urllib.parse
    
    current_password = (current_password or "").strip()
    new_password = (new_password or "").strip()
    confirm_new_password = (confirm_new_password or "").strip()
    
    settings_to_update = {
        "lang": lang,
        "hub_name": hub_name,
        "primary_color": primary_color,
        "accent_color": accent_color,
        "persona_admin": persona_admin,
        "persona_viewer": persona_viewer,
        "client_can_delete_own": client_can_delete_own,
        "client_can_edit_own": client_can_edit_own,
        "default_view_mode": default_view_mode,
        "default_shadows": default_shadows,
        "default_shadows_soft": default_shadows_soft,
        "default_shadow_transparency": default_shadow_transparency,
        "default_sun_intensity": default_sun_intensity,
        "default_ambient_intensity": default_ambient_intensity,
        "default_auto_rotate": default_auto_rotate,
        "max_upload_size": max_upload_size,
        "buymeacoffee_url": buymeacoffee_url
    }
    
    if current_password:
        settings = get_all_settings()
        db_password = settings.get("admin_password")
        expected_password = db_password if db_password else ADMIN_PASSWORD
        
        if current_password != expected_password:
            err_msg = "Nieprawidłowe obecne hasło" if lang == "pl" else "Incorrect current password"
            return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
            
        if not new_password:
            err_msg = "Nowe hasło nie może być puste" if lang == "pl" else "New password cannot be empty"
            return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
            
        if new_password != confirm_new_password:
            err_msg = "Nowe hasła nie są identyczne" if lang == "pl" else "New passwords do not match"
            return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
            
        settings_to_update["admin_password"] = new_password

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        if logo and logo.filename:
            ext = logo.filename.split('.')[-1].lower()
            if ext in ('png', 'jpg', 'jpeg', 'svg', 'webp'):
                logo_filename = f"custom_logo.{ext}"
                logo_path = os.path.join(DATA_DIR, logo_filename)
                with open(logo_path, "wb") as buffer:
                    shutil.copyfileobj(logo.file, buffer)
                settings_to_update["logo_filename"] = logo_filename
                
        if favicon and favicon.filename:
            ext = favicon.filename.split('.')[-1].lower()
            if ext in ('png', 'ico', 'svg', 'webp'):
                favicon_filename = f"custom_favicon.{ext}"
                favicon_path = os.path.join(DATA_DIR, favicon_filename)
                with open(favicon_path, "wb") as buffer:
                    shutil.copyfileobj(favicon.file, buffer)
                settings_to_update["favicon_filename"] = favicon_filename
        
        for k, v in settings_to_update.items():
            cur.execute("INSERT OR REPLACE INTO global_settings (key, value) VALUES (?, ?)", (k, str(v)))
            
        conn.commit()
    except Exception as e:
        print(f"Error saving settings: {e}")
        err_msg = "Błąd zapisu ustawień" if lang == "pl" else "Error saving settings"
        return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
        
    return RedirectResponse(url="/?success=1", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/admin/change_password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_new_password: str = Form(...)
):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    import urllib.parse
    
    settings = get_all_settings()
    lang = request.cookies.get("lang", settings.get("lang", "pl"))
    if lang not in ("pl", "en"):
        lang = "pl"
        
    current_password = current_password.strip()
    new_password = new_password.strip()
    confirm_new_password = confirm_new_password.strip()
    
    db_password = settings.get("admin_password")
    expected_password = db_password if db_password else ADMIN_PASSWORD
    
    if current_password != expected_password:
        err_msg = "Nieprawidłowe obecne hasło" if lang == "pl" else "Incorrect current password"
        return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
        
    if not new_password:
        err_msg = "Nowe hasło nie może być puste" if lang == "pl" else "New password cannot be empty"
        return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
        
    if new_password != confirm_new_password:
        err_msg = "Nowe hasła nie są identyczne" if lang == "pl" else "New passwords do not match"
        return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO global_settings (key, value) VALUES (?, ?)", ("admin_password", new_password))
        conn.commit()
    except Exception as e:
        print(f"Error saving password: {e}")
        err_msg = "Błąd zapisu hasła" if lang == "pl" else "Error saving password"
        return RedirectResponse(url=f"/?error={urllib.parse.quote(err_msg)}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
        
    success_msg = "Hasło zostało pomyślnie zmienione!" if lang == "pl" else "Password changed successfully!"
    return RedirectResponse(url=f"/?success_msg={urllib.parse.quote(success_msg)}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/api/lang/change/{lang}")
async def change_language(lang: str, request: Request):
    if lang not in ("pl", "en"):
        lang = "pl"
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="lang", value=lang, max_age=86400 * 365, samesite="lax")
    return response

@app.get("/favicon.ico")
async def get_favicon():
    settings = get_all_settings()
    custom_fav = settings.get("favicon_filename")
    if custom_fav:
        custom_path = os.path.join(DATA_DIR, custom_fav)
        if os.path.exists(custom_path):
            ext = custom_fav.split('.')[-1].lower()
            media_type = "image/x-icon" if ext == 'ico' else (f"image/{ext}" if ext != 'svg' else "image/svg+xml")
            return FileResponse(custom_path, media_type=media_type)
            
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.post("/delete/{filename}")
async def delete_model(filename: str, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # 1. Delete the physical file
        os.remove(file_path)
        
        # 2. Clean up associated comments, replies, and settings in the DB
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            # Delete replies connected to comments of this model
            cur.execute("""
                DELETE FROM comment_replies 
                WHERE comment_id IN (SELECT id FROM comments WHERE model_name = ?)
            """, (filename,))
            # Delete the comments
            cur.execute("DELETE FROM comments WHERE model_name = ?", (filename,))
            # Delete model settings
            cur.execute("DELETE FROM model_settings WHERE model_name = ?", (filename,))
            conn.commit()
        except Exception as e:
            print(f"Error cleaning up DB for deleted model {filename}: {e}")
        finally:
            conn.close()
            
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="File not found")

# Schemas for comments
class CameraState(BaseModel):
    x: float
    y: float
    z: float

class CommentCreate(BaseModel):
    x: float
    y: float
    z: float
    camera: CameraState
    target: CameraState
    text: str
    author_name: str

class CommentUpdate(BaseModel):
    text: str
    author_name: str

class ReplyCreate(BaseModel):
    text: str
    author_name: str

class ModelPasswordRequest(BaseModel):
    password_enabled: bool
    password_value: str

class PasswordVerifyRequest(BaseModel):
    password: str

# Comment endpoints
@app.get("/api/comments/{filename}")
async def get_comments(filename: str, request: Request):
    if not check_model_password_auth(filename, request):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, x, y, z, camera_x, camera_y, camera_z, target_x, target_y, target_z, text, author_name, author_type, created_at 
        FROM comments WHERE model_name = ? ORDER BY id ASC
    """, (filename,))
    rows = cur.fetchall()
    
    comments = []
    for r in rows:
        comment = {
            "id": r[0],
            "x": r[1], "y": r[2], "z": r[3],
            "camera": {"x": r[4], "y": r[5], "z": r[6]},
            "target": {"x": r[7], "y": r[8], "z": r[9]},
            "text": r[10],
            "author_name": r[11],
            "author_type": r[12],
            "created_at": r[13],
            "replies": [],
            "has_both_parties": False
        }
        
        cur.execute("""
            SELECT id, text, author_name, author_type, created_at
            FROM comment_replies WHERE comment_id = ? ORDER BY id ASC
        """, (r[0],))
        reply_rows = cur.fetchall()
        
        author_types = {r[12]}
        for rr in reply_rows:
            comment["replies"].append({
                "id": rr[0],
                "text": rr[1],
                "author_name": rr[2],
                "author_type": rr[3],
                "created_at": rr[4]
            })
            author_types.add(rr[3])
        
        comment["has_both_parties"] = len(author_types) > 1
        comments.append(comment)
    
    conn.close()
    return comments

@app.post("/api/comments/{filename}")
async def create_comment(filename: str, comment: CommentCreate, request: Request):
    if not check_model_password_auth(filename, request):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    author_type = "architect" if is_authenticated(request) else "client"
    
    author_name = comment.author_name.strip()
    if not author_name:
        raise HTTPException(status_code=400, detail="Nazwa autora jest wymagana")
        
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO comments (model_name, x, y, z, camera_x, camera_y, camera_z, target_x, target_y, target_z, text, author_name, author_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename, comment.x, comment.y, comment.z,
        comment.camera.x, comment.camera.y, comment.camera.z,
        comment.target.x, comment.target.y, comment.target.z,
        comment.text, author_name, author_type, created_at
    ))
    conn.commit()
    comment_id = cur.lastrowid
    conn.close()
    
    return {
        "id": comment_id,
        "author_type": author_type,
        "created_at": created_at
    }

@app.put("/api/comments/{filename}/{comment_id}")
async def update_comment(filename: str, comment_id: int, comment: CommentUpdate, request: Request):
    if not check_model_password_auth(filename, request):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT author_type FROM comments WHERE id = ? AND model_name = ?", (comment_id, filename))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Komentarz nie istnieje")
        
    db_author_type = row[0]
    req_is_admin = is_authenticated(request)
    settings = get_all_settings()
    
    if not req_is_admin:
        client_can_edit = settings.get("client_can_edit_own", "1") == "1"
        if not client_can_edit:
            conn.close()
            raise HTTPException(status_code=403, detail="Edycja komentarzy przez klienta jest wyłączona")
        if db_author_type == "architect":
            conn.close()
            raise HTTPException(status_code=403, detail="Klient nie może edytować komentarzy architekta")
    if db_author_type == "client" and req_is_admin:
        conn.close()
        raise HTTPException(status_code=403, detail="Architekt nie może edytować komentarzy klienta")
        
    author_name = comment.author_name.strip()
    if not author_name:
        conn.close()
        raise HTTPException(status_code=400, detail="Nazwa autora jest wymagana")
        
    cur.execute("UPDATE comments SET text = ?, author_name = ? WHERE id = ?", (comment.text, author_name, comment_id))
    conn.commit()
    conn.close()
    
    return {"status": "updated"}

@app.delete("/api/comments/{filename}/{comment_id}")
async def delete_comment(filename: str, comment_id: int, request: Request):
    if not check_model_password_auth(filename, request):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT author_type FROM comments WHERE id = ? AND model_name = ?", (comment_id, filename))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Komentarz nie istnieje")
        
    db_author_type = row[0]
    req_is_admin = is_authenticated(request)
    settings = get_all_settings()
    
    if not req_is_admin:
        client_can_delete = settings.get("client_can_delete_own", "1") == "1"
        if not client_can_delete:
            conn.close()
            raise HTTPException(status_code=403, detail="Usuwanie komentarzy przez klienta jest wyłączone")
        if db_author_type == "architect":
            conn.close()
            raise HTTPException(status_code=403, detail="Klient nie może usuwać komentarzy architekta")
        
    cur.execute("DELETE FROM comment_replies WHERE comment_id = ?", (comment_id,))
    cur.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    
    return {"status": "deleted"}

@app.post("/api/comments/{filename}/{comment_id}/replies")
async def create_reply(filename: str, comment_id: int, reply: ReplyCreate, request: Request):
    if not check_model_password_auth(filename, request):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    author_type = "architect" if is_authenticated(request) else "client"
    
    author_name = reply.author_name.strip()
    if not author_name:
        raise HTTPException(status_code=400, detail="Nazwa autora jest wymagana")
    
    text = reply.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Treść odpowiedzi jest wymagana")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM comments WHERE id = ? AND model_name = ?", (comment_id, filename))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Komentarz nie istnieje")
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        INSERT INTO comment_replies (comment_id, text, author_name, author_type, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (comment_id, text, author_name, author_type, created_at))
    conn.commit()
    reply_id = cur.lastrowid
    conn.close()
    
    return {"id": reply_id, "author_type": author_type, "created_at": created_at}

@app.delete("/api/comments/{filename}/{comment_id}/replies/{reply_id}")
async def delete_reply(filename: str, comment_id: int, reply_id: int, request: Request):
    if not check_model_password_auth(filename, request):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT author_type FROM comment_replies WHERE id = ? AND comment_id = ?", (reply_id, comment_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Odpowiedź nie istnieje")
    
    db_author_type = row[0]
    req_is_admin = is_authenticated(request)
    settings = get_all_settings()
    
    if not req_is_admin:
        client_can_delete = settings.get("client_can_delete_own", "1") == "1"
        if not client_can_delete:
            conn.close()
            raise HTTPException(status_code=403, detail="Usuwanie komentarzy przez klienta jest wyłączone")
        if db_author_type == "architect":
            conn.close()
            raise HTTPException(status_code=403, detail="Klient nie może usuwać odpowiedzi architekta")
    
    cur.execute("DELETE FROM comment_replies WHERE id = ?", (reply_id,))
    conn.commit()
    conn.close()
    
    return {"status": "deleted"}

@app.post("/api/settings/{filename}/toggle_comments")
async def toggle_comments(filename: str, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT comments_enabled FROM model_settings WHERE model_name = ?", (filename,))
    row = cur.fetchone()
    
    new_state = 0
    if row is None:
        cur.execute("INSERT INTO model_settings (model_name, comments_enabled) VALUES (?, 0)", (filename,))
        new_state = 0
    else:
        new_state = 1 if row[0] == 0 else 0
        cur.execute("UPDATE model_settings SET comments_enabled = ? WHERE model_name = ?", (new_state, filename))
        
    conn.commit()
    conn.close()
    return {"comments_enabled": bool(new_state)}

@app.post("/api/settings/{filename}/password")
async def update_model_password(filename: str, req: ModelPasswordRequest, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT comments_enabled FROM model_settings WHERE model_name = ?", (filename,))
    row = cur.fetchone()
    
    enabled_val = 1 if req.password_enabled else 0
    pwd_val = req.password_value.strip()
    
    if row is None:
        cur.execute(
            "INSERT INTO model_settings (model_name, comments_enabled, password_enabled, password_value) VALUES (?, 1, ?, ?)",
            (filename, enabled_val, pwd_val)
        )
    else:
        cur.execute(
            "UPDATE model_settings SET password_enabled = ?, password_value = ? WHERE model_name = ?",
            (enabled_val, pwd_val, filename)
        )
        
    conn.commit()
    conn.close()
    return {"status": "success", "password_enabled": req.password_enabled, "password_value": pwd_val}

@app.post("/api/settings/{filename}/verify_password")
async def verify_model_password(filename: str, req: PasswordVerifyRequest, request: Request):
    settings = get_all_settings()
    lang = request.cookies.get("lang", settings.get("lang", "pl"))
    if lang not in ("pl", "en"):
        lang = "pl"
        
    valid = check_model_password_auth(filename, request, req.password)
    if not valid:
        err_msg = "Nieprawidłowe hasło dostępu" if lang == "pl" else "Incorrect access password"
        raise HTTPException(status_code=403, detail=err_msg)
    return {"status": "success", "valid": True}

# Public view endpoints (no auth required)
@app.get("/show/{filename}", response_class=HTMLResponse)
async def show_model(filename: str, request: Request):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Model nie istnieje")
    
    m_settings = get_model_settings(filename)
    is_admin = is_authenticated(request)
    password_required = m_settings["password_enabled"] and not is_admin
    
    return templates.TemplateResponse("show.html", {
        "request": request,
        "filename": filename,
        "is_embed": False,
        "is_architect": is_admin,
        "comments_enabled": m_settings["comments_enabled"],
        "password_required": password_required
    })

@app.get("/embed/{filename}", response_class=HTMLResponse)
async def embed_model(filename: str, request: Request):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Model nie istnieje")
        
    m_settings = get_model_settings(filename)
    is_admin = is_authenticated(request)
    password_required = m_settings["password_enabled"] and not is_admin
    
    return templates.TemplateResponse("show.html", {
        "request": request,
        "filename": filename,
        "is_embed": True,
        "is_architect": is_admin,
        "comments_enabled": m_settings["comments_enabled"],
        "password_required": password_required
    })

@app.get("/raw/{filename}")
async def raw_model(filename: str, request: Request, password: Optional[str] = None):
    if not check_model_password_auth(filename, request, password):
        raise HTTPException(status_code=403, detail="Forbidden - Password required")
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="model/gltf-binary")

@app.get("/logo.png")
async def get_logo():
    settings = get_all_settings()
    custom_logo = settings.get("logo_filename")
    if custom_logo:
        custom_path = os.path.join(DATA_DIR, custom_logo)
        if os.path.exists(custom_path):
            ext = custom_logo.split('.')[-1].lower()
            media_type = f"image/{ext}" if ext != 'svg' else "image/svg+xml"
            return FileResponse(custom_path, media_type=media_type)
            
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")
