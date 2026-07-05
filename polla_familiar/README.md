# Polla Familiar

App de Streamlit para una polla familiar de marcadores de fútbol. Usa un archivo JSON local como persistencia temporal y concentra todo el acceso a datos en `storage.py`, para que luego puedas reemplazar esa capa por una base de datos real sin tocar las páginas.

## Instalación

```bash
cd polla_familiar
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Primer acceso

La app crea automáticamente un usuario administrador inicial si no hay usuarios:

- Usuario: `adminp0lla`
- Contrasena: `p0lla2026`

Desde la página Admin puedes crear partidos manualmente y cargar marcadores finales.

## Estructura

- `app.py`: login y registro.
- `auth.py`: hash/verificación de contraseñas y helpers de sesión.
- `storage.py`: única capa de lectura/escritura del JSON local.
- `scoring.py`: reglas puras de puntuación.
- `pages/`: páginas de predicciones, tabla, analítica y admin.
- `data/polla_data.json`: se crea automáticamente al iniciar la app.
