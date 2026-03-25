from pydantic import BaseModel


class Settings(BaseModel):
    """
    Purpose:
    - Hold runtime configuration for application bootstrap.

    Responsibilities:
    - Expose typed settings consumed by container wiring.

    Inputs:
    - app_name: str

    Outputs:
    - Settings model.

    Constraints:
    - Defaults must support local development startup.
    """

    app_name: str = "Notiq"
