"""ORM model registry.

Import every model module here so its tables are registered on
``app.database.base.Base.metadata``. Alembic imports this package to compare
the models with the database when generating migrations.
"""

from app.models.instance_settings import InstanceSettings
from app.models.password_reset import PasswordResetToken
from app.models.session import UserSession
from app.models.trusted_device import TrustedDevice
from app.models.user import User

__all__ = ["InstanceSettings", "PasswordResetToken", "TrustedDevice", "User", "UserSession"]
