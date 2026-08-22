from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from sagduyu.engine import CoordinationEngine
from sagduyu.models import (
    CoordinationAlert,
    EventAnalysisRequest,
    EventAnalysisResult,
    ModerationDecision,
    ModerationDecisionCreate,
    ReplayResult,
    ReviewStatus,
)
from sagduyu.scenarios import SCENARIOS, load_scenario
from sagduyu.store import AlertNotFoundError, InMemoryModerationStore
from sagduyu.text_safety import CourtesyAssessment, CourtesyChecker, CourtesyCheckRequest


def create_app(
    *,
    engine: CoordinationEngine | None = None,
    store: InMemoryModerationStore | None = None,
) -> FastAPI:
    engine_instance = engine or CoordinationEngine()
    store_instance = store or InMemoryModerationStore()
    courtesy_checker = CourtesyChecker()
    app = FastAPI(
        title="SAĞDUYU Moderasyon API",
        version="0.1.0",
        description="Açıklanabilir koordineli manipülasyon karar destek API'si.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.engine = engine_instance
    app.state.store = store_instance

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "engine_version": engine_instance.version}

    @app.get("/api/v1/scenarios", tags=["replay"])
    def list_scenarios() -> list[str]:
        return sorted(SCENARIOS)

    @app.post(
        "/api/v1/text/courtesy-check",
        response_model=CourtesyAssessment,
        tags=["text-safety"],
    )
    def check_courtesy(request: CourtesyCheckRequest) -> CourtesyAssessment:
        return courtesy_checker.assess(request.text)

    @app.post("/api/v1/replays/{scenario}", response_model=ReplayResult, tags=["replay"])
    def replay_scenario(scenario: str) -> ReplayResult:
        try:
            events = load_scenario(scenario)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        alerts = engine_instance.analyze(events)
        store_instance.upsert_alerts(alerts)
        return ReplayResult(
            scenario=scenario,
            event_count=len(events),
            alert_count=len(alerts),
            alerts=alerts,
        )

    @app.post(
        "/api/v1/analyses",
        response_model=EventAnalysisResult,
        tags=["analysis"],
    )
    def analyze_events(request: EventAnalysisRequest) -> EventAnalysisResult:
        alerts = engine_instance.analyze(request.events)
        store_instance.upsert_alerts(alerts)
        return EventAnalysisResult(
            source_id=request.source_id,
            event_count=len(request.events),
            alert_count=len(alerts),
            alerts=alerts,
        )

    @app.get("/api/v1/alerts", response_model=list[CoordinationAlert], tags=["moderation"])
    def list_alerts(
        min_risk_score: float = Query(default=0.0, ge=0.0, le=100.0),
        review_status: ReviewStatus | None = None,
    ) -> list[CoordinationAlert]:
        return store_instance.list_alerts(
            min_risk_score=min_risk_score,
            status=review_status,
        )

    @app.get(
        "/api/v1/alerts/{alert_id}",
        response_model=CoordinationAlert,
        tags=["moderation"],
    )
    def get_alert(alert_id: str) -> CoordinationAlert:
        try:
            return store_instance.get_alert(alert_id)
        except AlertNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="alert not found",
            ) from error

    @app.post(
        "/api/v1/alerts/{alert_id}/decisions",
        response_model=ModerationDecision,
        status_code=status.HTTP_201_CREATED,
        tags=["moderation"],
    )
    def create_decision(
        alert_id: str,
        request: ModerationDecisionCreate,
    ) -> ModerationDecision:
        try:
            return store_instance.add_decision(alert_id, request)
        except AlertNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="alert not found",
            ) from error

    @app.get(
        "/api/v1/alerts/{alert_id}/decisions",
        response_model=list[ModerationDecision],
        tags=["moderation"],
    )
    def list_decisions(alert_id: str) -> list[ModerationDecision]:
        try:
            return store_instance.list_decisions(alert_id)
        except AlertNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="alert not found",
            ) from error

    return app


app = create_app()
