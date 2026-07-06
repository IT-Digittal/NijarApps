"""Tests de coherencia del paquete consolidado.

Validan que toda la documentación, los manifests y los seeds están
internamente consistentes. Estos tests son el "test de SAT" — si pasan,
el paquete está listo para entrega administrativa.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# Raíz del proyecto (../..)
REPO = Path(__file__).resolve().parent.parent


class TestDocumentacionPresente:
    """Todos los entregables documentales del Pliego deben existir."""

    @pytest.mark.parametrize("doc", [
        "README.md",
        "docs/architecture/arquitectura-global.md",
        "docs/architecture/diagramas-tecnicos.md",
        "docs/architecture/decisiones-tecnicas.md",
        "docs/architecture/dependencias-terceros.md",
        "docs/backend/manual-tecnico-backend.md",
        "docs/chatbot/manual-tecnico-chatbot.md",
        "docs/accessibility/wcag-2.1-AA-compliance.md",
        "docs/security/plan-pentest-sat.md",
        "docs/operations/runbook.md",
        "docs/operations/disaster-recovery.md",
        "docs/operations/sla-monitoring.md",
        "docs/operations/business-continuity.md",
        "docs/MAPA-FUNCIONAL.md",
        "docs/api/openapi.yaml",
        "docs/database/schema.sql",
    ])
    def test_documento_existe(self, doc):
        path = REPO / doc
        assert path.is_file(), f"Falta documento entregable: {doc}"
        assert path.stat().st_size > 100, f"Documento sospechosamente pequeño: {doc}"


class TestInfraestructuraComoCodigo:
    """Terraform y K8s manifests deben estar presentes y ser parseables."""

    @pytest.mark.parametrize("tf", [
        "infra/terraform/variables.tf",
        "infra/terraform/main.tf",
        "infra/terraform/network.tf",
        "infra/terraform/rds.tf",
        "infra/terraform/eks.tf",
        "infra/terraform/services.tf",
        "infra/terraform/outputs.tf",
    ])
    def test_terraform_existe(self, tf):
        assert (REPO / tf).is_file(), f"Falta archivo Terraform: {tf}"

    @pytest.mark.parametrize("manifest", [
        "infra/k8s/00-namespace.yaml",
        "infra/k8s/10-api-deployment.yaml",
        "infra/k8s/15-config.yaml",
        "infra/k8s/20-external-secrets.yaml",
        "infra/k8s/30-workers.yaml",
        "infra/k8s/40-mqtt-rasa.yaml",
        "infra/k8s/50-ingress.yaml",
    ])
    def test_k8s_manifest_es_yaml_valido(self, manifest):
        path = REPO / manifest
        assert path.is_file(), f"Falta manifest: {manifest}"
        docs = list(yaml.safe_load_all(path.read_text()))
        assert all(d is None or isinstance(d, dict) for d in docs), \
            f"YAML inválido en {manifest}"
        # cada documento aparte de la posición vacía debe tener apiVersion+kind
        for d in docs:
            if d:
                assert "apiVersion" in d, f"{manifest} tiene un doc sin apiVersion"
                assert "kind" in d, f"{manifest} tiene un doc sin kind"


class TestObservabilidad:

    @pytest.mark.parametrize("f", [
        "infra/observability/prometheus-values.yaml",
        "infra/observability/prometheus-servicemonitor.yaml",
        "infra/observability/alerts.yaml",
        "infra/observability/loki-values.yaml",
    ])
    def test_yaml_observability_valido(self, f):
        path = REPO / f
        assert path.is_file()
        list(yaml.safe_load_all(path.read_text()))  # no debe lanzar

    @pytest.mark.parametrize("dash", [
        "infra/observability/grafana-dashboards/api-overview.json",
        "infra/observability/grafana-dashboards/smart-office.json",
        "infra/observability/grafana-dashboards/big-data.json",
        "infra/observability/grafana-dashboards/chatbot.json",
        "infra/observability/grafana-dashboards/infraestructura.json",
    ])
    def test_dashboard_grafana_es_json_valido(self, dash):
        data = json.loads((REPO / dash).read_text())
        assert "title" in data
        assert "uid" in data
        assert "panels" in data
        assert len(data["panels"]) > 0


class TestRasaArtefactos:
    """Comprueba que los artefactos Rasa generados son válidos."""

    @pytest.mark.parametrize("f", [
        "rasa/config.yml",
        "rasa/credentials.yml",
        "rasa/endpoints.yml",
        "rasa/domain.yml",
        "rasa/data/nlu.yml",
        "rasa/data/rules.yml",
        "rasa/data/stories.yml",
    ])
    def test_yaml_rasa_valido(self, f):
        path = REPO / f
        assert path.is_file(), f"Falta archivo Rasa: {f}"
        data = yaml.safe_load(path.read_text())
        assert data is not None

    def test_domain_y_nlu_tienen_mismos_intents(self):
        domain = yaml.safe_load((REPO / "rasa/domain.yml").read_text())
        nlu = yaml.safe_load((REPO / "rasa/data/nlu.yml").read_text())
        domain_intents = set(domain.get("intents", []))
        nlu_intents = {item["intent"] for item in nlu.get("nlu", []) if "intent" in item}
        # nlu_fallback solo está en domain
        domain_intents.discard("nlu_fallback")
        # Todos los intents del NLU deben estar en el domain
        assert nlu_intents.issubset(domain_intents), (
            f"Intents en NLU sin definir en domain: {nlu_intents - domain_intents}"
        )


class TestCICD:

    @pytest.mark.parametrize("wf", [
        ".github/workflows/ci.yml",
        ".github/workflows/cd.yml",
        ".github/workflows/security-nightly.yml",
    ])
    def test_workflow_existe(self, wf):
        path = REPO / wf
        assert path.is_file(), f"Falta workflow: {wf}"
        data = yaml.safe_load(path.read_text())
        assert "jobs" in data, f"{wf} sin jobs"


class TestFrontend:

    @pytest.mark.parametrize("f", [
        "frontend/dashboard/index.html",
        "frontend/dashboard/assets/api-client.js",
        "frontend/dashboard/assets/panel-live.js",
        "frontend/dashboard/assets/panel-gestion.js",
        "frontend/dashboard/assets/panel-mapa.js",
        "frontend/dashboard/assets/verticales-live.js",
        "frontend/totem/index.html",
        "frontend/totem/assets/totem.css",
        "frontend/totem/assets/totem.js",
        "frontend/totem/assets/i18n.js",
    ])
    def test_archivo_frontend_existe(self, f):
        assert (REPO / f).is_file(), f"Falta archivo frontend: {f}"

    def test_totem_tiene_idiomas_obligatorios(self):
        i18n = (REPO / "frontend/totem/assets/i18n.js").read_text()
        for lang in ("es:", "en:", "de:", "fr:"):
            assert lang in i18n, f"i18n del tótem no incluye '{lang}'"


class TestADRsCompletos:

    def test_hay_al_menos_21_adrs(self):
        adrs = (REPO / "docs/architecture/decisiones-tecnicas.md").read_text()
        # Cada ADR comienza con "## ADR-NNN"
        import re
        matches = re.findall(r"^## ADR-(\d+)", adrs, re.MULTILINE)
        assert len(matches) >= 21, (
            f"Se esperan al menos 21 ADRs, se encontraron {len(matches)}"
        )
