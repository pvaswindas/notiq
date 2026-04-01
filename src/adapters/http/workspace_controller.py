from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.use_cases.create_workspace import CreateWorkspaceInput, CreateWorkspaceUseCase
from src.application.use_cases.get_workspace import GetWorkspaceInput, GetWorkspaceUseCase
from src.application.use_cases.list_workspaces import ListWorkspacesInput, ListWorkspacesUseCase
from src.domain.entities.workspace import Workspace


class CreateWorkspaceRequest(BaseModel):
    """HTTP payload for creating a workspace in the compatibility API surface.

    Purpose:
    - Capture the minimal user-provided identity (`name`) required to create a
      workspace.

    Constraints:
    - Unknown fields are rejected.
    - `name` must be non-empty.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)


class WorkspaceResponse(BaseModel):
    """Stable HTTP representation of a workspace resource.

    Architectural role:
    - Outbound DTO that isolates API contracts from internal domain model
      implementation details.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str


class WorkspaceControllerFactory:
    """Compose workspace HTTP routes backed by application use cases.

    Responsibilities:
    - Validate protocol-level concerns (path/body schema).
    - Translate use-case errors into HTTP-friendly status codes.
    - Keep routing logic thin and free from business orchestration.
    """

    def __init__(
        self,
        create_workspace_use_case: CreateWorkspaceUseCase,
        get_workspace_use_case: GetWorkspaceUseCase,
        list_workspaces_use_case: ListWorkspacesUseCase,
    ) -> None:
        """Store use-case dependencies used by workspace route handlers.

        Args:
            create_workspace_use_case: Creates new workspace records.
            get_workspace_use_case: Fetches one workspace by id.
            list_workspaces_use_case: Lists all workspaces.
        """

        self._create_workspace_use_case = create_workspace_use_case
        self._get_workspace_use_case = get_workspace_use_case
        self._list_workspaces_use_case = list_workspaces_use_case

    def build(self) -> APIRouter:
        """Build workspace router with create/get/list endpoints.

        Returns:
            APIRouter: Router exposing workspace compatibility endpoints.

        Important:
        - Business validation remains in use cases.
        - Route-level logic should only map protocol concerns and errors.
        """

        router = APIRouter(tags=["workspaces"])

        @router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
        async def create_workspace(request: CreateWorkspaceRequest) -> WorkspaceResponse:
            """Create a workspace and return its API representation.

            Args:
                request: Validated request body containing workspace name.

            Returns:
                WorkspaceResponse: Created workspace DTO.

            Internal flow:
            - Delegates normalization and creation policy to use case.
            - Converts input validation failures to HTTP 400.
            """

            try:
                workspace = await self._create_workspace_use_case.execute(
                    CreateWorkspaceInput(
                        name=request.name,
                        actor_id=None,
                        audit_metadata={"source": "workspace_api"},
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return _to_workspace_response(workspace)

        @router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
        async def get_workspace(workspace_id: str) -> WorkspaceResponse:
            """Fetch one workspace by id.

            Args:
                workspace_id: Workspace identifier from URL path.

            Returns:
                WorkspaceResponse: Existing workspace DTO.

            Edge cases:
            - Blank/invalid identifiers return HTTP 400.
            - Unknown workspace returns HTTP 404.
            """

            try:
                workspace = await self._get_workspace_use_case.execute(GetWorkspaceInput(id=workspace_id))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            if workspace is None:
                raise HTTPException(status_code=404, detail="workspace not found")

            return _to_workspace_response(workspace)

        @router.get("/workspaces", response_model=list[WorkspaceResponse])
        async def list_workspaces() -> list[WorkspaceResponse]:
            """List all workspaces exposed by compatibility API routes.

            Returns:
                list[WorkspaceResponse]: Workspace DTOs in repository-defined order.

            Internal flow:
            - Delegates retrieval to listing use case.
            - Applies one-way mapping from domain entity to API DTO.
            """

            workspaces = await self._list_workspaces_use_case.execute(ListWorkspacesInput())
            return [_to_workspace_response(workspace) for workspace in workspaces]

        return router


def _to_workspace_response(workspace: Workspace) -> WorkspaceResponse:
    """Map workspace domain entity into HTTP response DTO.

    Args:
        workspace: Domain workspace model.

    Returns:
        WorkspaceResponse: API-safe projection of workspace fields.
    """

    return WorkspaceResponse(id=workspace.id, name=workspace.name)
