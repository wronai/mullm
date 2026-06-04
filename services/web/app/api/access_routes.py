from __future__ import annotations

from app import access_matrix
from app import resource_areas
from app.api.models import AccessMatrixBody
from fastapi import APIRouter

router = APIRouter()


@router.get("/resource-areas")
async def api_resource_areas():
    return {
        "areas": resource_areas.list_areas(),
        "groups": resource_areas.list_groups(),
        "labels": resource_areas.LABEL_VOCABULARY,
    }


@router.get("/resource-areas/roles")
async def api_role_scopes():
    return {"roles": resource_areas.DEFAULT_ROLE_SCOPES}


@router.get("/access/matrix")
async def access_matrix_get():
    return access_matrix.load_state()


@router.put("/access/matrix")
async def access_matrix_put(body: AccessMatrixBody):
    state = access_matrix.load_state()
    data = body.model_dump(exclude_unset=True)
    state.update(data)
    return {"ok": True, "state": access_matrix.save_state(state)}


@router.post("/access/matrix/reset")
async def access_matrix_reset():
    state = access_matrix.default_state()
    return {"ok": True, "state": access_matrix.save_state(state)}


@router.get("/access/diagnose/file-list")
async def access_diagnose_file_list():
    return access_matrix.diagnose_file_list_command()
