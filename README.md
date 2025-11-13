# Automox Desktop Dashboard

Aplicación de escritorio construida con PySide6 para visualizar en tiempo real los datos de Automox utilizando su API oficial. Permite autenticarse con API Key + Organization ID y consultar dispositivos, políticas, grupos, inventario de software, bitácora de eventos, backlog de parches y dispositivos con problemas.

## Requisitos

- Python 3.11+
- Dependencias del proyecto:
  - `PySide6`
  - `requests`

Instalación rápida:

```bash
python -m venv .venv
source .venv/bin/activate
pip install PySide6 requests
```

## Uso

1. Ejecuta la aplicación:

```bash
python main.py
```

2. Introduce tu **API Key** y **Organization ID** de Automox en el panel superior.
3. Selecciona un rango de fechas (Today, Yesterday, Last 7 days, Last 30 days o Custom) y pulsa **“Cargar datos”**.
4. Navega por las pestañas (Dashboard, Devices, Policies, Groups, Software, Activity Log, Pre-Patch, Troubleshooting) para analizar la información. Cada pestaña incluye filtrado avanzado y opción de exportar a CSV.
5. Atajos disponibles:
   - `Ctrl+R`: recargar datos desde la API.
   - `Ctrl+F`: enfocar la barra de búsqueda de la pestaña activa.
   - `Ctrl+E`: exportar a CSV el contenido de la pestaña activa.

La barra de estado muestra el resultado de cada carga (éxito, error de autenticación, rate limit, etc.).

## Empaquetado con PyInstaller

Para generar un ejecutable único en Windows:

```bash
pyinstaller --onefile --noconsole --name AutomoxDashboard --icon assets/app_icon.ico main.py
```

Asegúrate de incluir los recursos necesarios (iconos, estilos) mediante la opción `--add-data` o un archivo `.spec` personalizado si agregas recursos extra.
