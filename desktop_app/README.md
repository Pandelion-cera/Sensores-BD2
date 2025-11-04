# Desktop Application - Sensor Management System

Desktop application built with PyQt6 for managing climate sensors and measurements.

## Features

- User authentication (login/register)
- Dashboard with statistics
- Direct database connections (no API layer)
- Single executable build support

## Requirements

- Python 3.11+
- All databases running (MongoDB, Cassandra, Neo4j, Redis)
- Database initialization completed
- **Windows**: Microsoft Visual C++ Redistributable 2015-2022

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Windows DLL Error Fix:**
   If you get "DLL load failed" error:
   - Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Reinstall PyQt6: `pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip && pip install PyQt6`

3. **Ensure databases are running:**
```bash
# From project root
docker-compose up -d
```

4. **Initialize databases (if not already done):**
```bash
# From project root
cd backend
python scripts/init_databases.py
```

5. **Configure database connections:**
   - Edit `desktop_app/core/config.py` if database URLs differ from defaults

## Running the Application

### Development Mode

```bash
cd desktop_app
python main.py
```

### Build Executable

1. **Build with PyInstaller:**
```bash
cd desktop_app
pyinstaller build.spec
```

2. **For single-file executable**, uncomment the onefile section in `build.spec`:
```python
# Use the commented EXE section at the bottom of build.spec
```

3. **Run the executable:**
   - Windows: `dist/sensor_app.exe`
   - Linux/Mac: `dist/sensor_app`

## Application Structure

```
desktop_app/
├── main.py                 # Application entry point
├── core/                   # Core functionality
│   ├── config.py          # Configuration
│   ├── database.py        # Database manager
│   └── security.py        # Authentication/security
├── models/                 # Pydantic models
├── repositories/           # Data access layer
├── services/               # Business logic
├── ui/                     # PyQt6 UI components
│   ├── login_window.py    # Login/register dialog
│   ├── main_window.py     # Main application window
│   └── dashboard_widget.py # Dashboard widget
├── utils/                  # Utilities
│   └── session_manager.py # Session management
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### PyQt6 DLL Error on Windows

**Error**: `DLL load failed while importing QtCore`

**Solution**:
1. Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Reinstall PyQt6:
   ```bash
   pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y
   pip install PyQt6
   ```
3. If still failing, try installing from wheel:
   ```bash
   pip install --upgrade --force-reinstall PyQt6
   ```

### Database Connection Errors

- Verify Docker containers are running: `docker ps`
- Check database ports are available
- Verify connection strings in `config.py`

### Import Errors

- Ensure you're running from the `desktop_app` directory
- Verify all dependencies are installed: `pip install -r requirements.txt`

### PyQt6 Issues

- On Linux, you may need: `sudo apt-get install python3-pyqt6`
- On Mac, you may need: `brew install pyqt6`
