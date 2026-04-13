from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.base import BenutzerRolle


class BenutzerBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., max_length=150)
    email: EmailStr
    rolle: BenutzerRolle = BenutzerRolle.STANDARD


class BenutzerCreate(BenutzerBase):
    """Wird verwendet, wenn ein neuer Nutzer via Shibboleth angelegt wird."""
    shibboleth_id: str = Field(..., max_length=100)


class BenutzerResponse(BenutzerBase):
    """Wird an das Frontend zurückgegeben."""
    id: int
    shibboleth_id: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BenutzerRolleUpdate(BaseModel):
    """Payload für Admin: Rolle eines Benutzers ändern."""
    rolle: BenutzerRolle