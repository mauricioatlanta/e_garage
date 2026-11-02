from types import SimpleNamespace

from taller.services.workspace_service import WorkspaceService


def test_carwash_workspace_has_operational_navigation():
    config = SimpleNamespace(
        rubro_principal="DETAILING",
        rubros=["DETAILING"],
        usa_vehiculos=True,
        usa_servicios=True,
        get_effective_rubros=lambda: ["DETAILING"],
    )
    workspace = WorkspaceService.resolve(config, url_prefix="/cl/es")
    labels = [item["label"] for item in workspace["nav"]]
    urls = [item["url"] for item in workspace["nav"]]

    assert workspace["product_key"] == "CARWASH"
    assert labels == ["Inicio", "Caja", "Clientes", "Servicios", "Reportes", "Configuración", "Vehículos"]
    assert "/cl/es/documentos/form/" in urls
    assert "/cl/es/servicios/" in urls
