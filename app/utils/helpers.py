import re
import unicodedata
from datetime import date


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value) or "item"


def age_from_birthdate(birth_date):
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def status_badge(status):
    mapping = {
        "Aceito": "success",
        "Confirmado": "success",
        "Finalizado": "muted",
        "Pendente": "warning",
        "Solicitada": "warning",
        "Recusado": "danger",
        "Cancelado": "danger",
        "Contraproposta": "info",
    }
    return mapping.get(status, "info")
