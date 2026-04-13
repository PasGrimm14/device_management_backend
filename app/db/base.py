# Import Base and all models here so Alembic can detect them
from app.db.base_class import Base  # noqa: F401
from app.models import *  # noqa: F401, F403
