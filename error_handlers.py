import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ─── Logger global ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),                      # affiche dans le terminal
        logging.FileHandler("irrigation_errors.log")  # sauvegarde dans un fichier
    ]
)
logger = logging.getLogger("irrigation")


# ─── Exceptions personnalisées ─────────────────────────────────────────────────
class DatabaseError(Exception):
    """Erreur lors d'une opération sur la base de données SQLite."""
    pass

class ModelError(Exception):
    """Erreur lors du chargement ou de l'utilisation du modèle ML."""
    pass

class InvalidSensorData(Exception):
    """Les valeurs capteur sont en dehors des plages physiquement acceptables."""
    pass


# ─── Validation des données capteur ───────────────────────────────────────────
SENSOR_BOUNDS = {
    "soil_moisture":  (0.0,  100.0),
    "temperature":    (-20.0, 60.0),
    "humidity":       (0.0,  100.0),
    "rainfall":       (0.0,  500.0),
    "sunlight_hours": (0.0,   24.0),
}

def validate_sensor_data(data: dict) -> None:
    """
    Lève InvalidSensorData si une valeur est hors des bornes physiques.
    À appeler avant chaque prédiction.
    """
    for field, (low, high) in SENSOR_BOUNDS.items():
        value = data.get(field)
        if value is None:
            raise InvalidSensorData(f"Champ manquant : '{field}'")
        if not (low <= value <= high):
            raise InvalidSensorData(
                f"'{field}' = {value} hors plage [{low}, {high}]"
            )


# ─── Enregistrement des handlers sur l'app FastAPI ────────────────────────────
def register_error_handlers(app: FastAPI) -> None:
    """
    Appelle cette fonction dans main.py après avoir créé l'app :
        register_error_handlers(app)
    """

    @app.exception_handler(InvalidSensorData)
    async def invalid_sensor_handler(request: Request, exc: InvalidSensorData):
        logger.warning(f"Données capteur invalides : {exc}")
        return JSONResponse(status_code=422, content={
            "error": "invalid_sensor_data",
            "detail": str(exc)
        })

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        logger.error(f"Erreur base de données : {exc}")
        return JSONResponse(status_code=503, content={
            "error": "database_error",
            "detail": "Impossible d'accéder à la base de données. Réessayez."
        })

    @app.exception_handler(ModelError)
    async def model_error_handler(request: Request, exc: ModelError):
        logger.critical(f"Erreur modèle ML : {exc}")
        return JSONResponse(status_code=500, content={
            "error": "model_error",
            "detail": "Le modèle de prédiction est indisponible."
        })

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Erreur inattendue sur {request.url} : {exc}")
        return JSONResponse(status_code=500, content={
            "error": "internal_error",
            "detail": "Une erreur interne est survenue."
        })