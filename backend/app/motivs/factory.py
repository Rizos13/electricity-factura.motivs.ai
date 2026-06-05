from __future__ import annotations

from typing import Literal

from motivs_core import SyncPipeline, load_contract_yaml
from motivs_core.adapters.memory import (
    EnvSecrets,
    InMemoryRegistryStore,
    InMemoryRunRepository,
    InMemoryStorage,
)
from motivs_core.config import PipelineConfig

from backend.app.core.config import Settings
from backend.app.motivs.emitter import StructLogEmitter
from backend.app.motivs.registry_fs import FileSystemRegistryStore


ContractKind = Literal["factura", "ofertas"]


def build_pipeline(
    settings: Settings,
    kind: ContractKind,
    *,
    shadow_baseline_required: bool = False,
) -> tuple[SyncPipeline, InMemoryRunRepository]:
    contract_path = (
        settings.factura_contract_path if kind == "factura"
        else settings.ofertas_contract_path
    )
    contract = load_contract_yaml(contract_path.read_text())

    secrets = EnvSecrets({settings.tenant_slug: settings.hmac_key.encode()})
    repository = InMemoryRunRepository()
    if kind == "ofertas":
        registry_path = settings.artifact_dir / "registry" / "ofertas.jsonl"
        registry_store = FileSystemRegistryStore(registry_path)
    else:
        registry_store = InMemoryRegistryStore()
    pipeline = SyncPipeline(
        contract=contract,
        repository=repository,
        storage=InMemoryStorage(),
        secrets=secrets,
        emitter=StructLogEmitter(),
        registry_store=registry_store,
        config=PipelineConfig(
            tenant_slug=settings.tenant_slug,
            shadow_baseline_required=shadow_baseline_required,
        ),
    )
    return pipeline, repository
