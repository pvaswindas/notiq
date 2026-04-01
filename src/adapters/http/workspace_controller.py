from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.use_cases.create_workspace import CreateWorkspaceInput, CreateWorkspaceUseCase
from src.application.use_cases.get_workspace import GetWorkspaceInput, GetWorkspaceUseCase
from src.application.use_cases.list_workspaces import ListWorkspacesInput, ListWorkspacesUseCase
from src.domain.entities.workspace import Workspace


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str


class WorkspaceControllerFactory:
    def __init__(
        self,
        create_workspace_use_case: CreateWorkspaceUseCase,
        get_workspace_use_case: GetWorkspaceUseCase,
        list_workspaces_use_case: ListWorkspacesUseCase,
    ) -> None:
        self._create_workspace_use_case = create_workspace_use_case
        self._get_workspace_use_case = get_workspace_use_case
        self._list_workspaces_use_case = list_workspaces_use_case

    def build(self) -> APIRouter:
        router = APIRouter(tags=["workspaces"])

        @router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
        async def create_workspace(request: CreateWorkspaceRequest) -> WorkspaceResponse:
            try:
                workspace = await self._create_workspace_use_case.execute(
                    CreateWorkspaceInput(name=request.name)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return _to_workspace_response(workspace)

        @router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
        async def get_workspace(workspace_id: str) -> WorkspaceResponse:
            try:
                workspace = await self._get_workspace_use_case.execute(GetWorkspaceInput(id=workspace_id))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            if workspace is None:
                raise HTTPException(status_code=404, detail="workspace not found")

            return _to_workspace_response(workspace)

        @router.get("/workspaces", response_model=list[WorkspaceResponse])
        async def list_workspaces() -> list[WorkspaceResponse]:
            workspaces = await self._list_workspaces_use_case.execute(ListWorkspacesInput())
            return [_to_workspace_response(workspace) for workspace in workspaces]

        return router


def _to_workspace_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(id=workspace.id, name=workspace.name)
