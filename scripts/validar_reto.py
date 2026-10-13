from datetime import date, datetime, timezone


def validate_prediction(record, last_draw, today=None):
    """Validate a new prediction; existing historical records are not revalidated."""
    if today is None:
        today = datetime.now(timezone.utc).date()
    target = record.get("target")
    nums = record.get("nums")
    created = record.get("created")
    window = record.get("window")
    history_until = record.get("historyUntil")
    if not isinstance(target, str) or not isinstance(created, str) or not isinstance(history_until, str):
        raise ValueError("Faltan fechas obligatorias.")
    target_date = date.fromisoformat(target)
    created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
    if created_at.tzinfo is None:
        raise ValueError("Fecha de creación sin zona horaria.")
    if created_at.astimezone(timezone.utc).date() > today:
        raise ValueError("La fecha de creación está en el futuro.")
    if not (history_until < target and target > last_draw and created_at.date() <= target_date):
        raise ValueError("Solo se aceptan predicciones para sorteos aún no presentes en el histórico.")
    if not isinstance(nums, list) or len(nums) != 6 or any(type(n) is not int or not 1 <= n <= 49 for n in nums) or len(set(nums)) != 6:
        raise ValueError("Combinación inválida.")
    if type(window) is not int or window not in (5, 20, 50, 100, 365, 500, 1000, 99999):
        raise ValueError("Ventana histórica inválida.")
