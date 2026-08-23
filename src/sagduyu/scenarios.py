from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sagduyu.models import (
    CoordinationContext,
    CoordinationContextType,
    EventType,
    SocialEvent,
)


def coordinated_campaign() -> list[SocialEvent]:
    base = datetime(2025, 6, 15, 9, 0, tzinfo=UTC)
    events: list[SocialEvent] = []
    accounts = [f"campaign_{index:02d}" for index in range(1, 9)]
    targets = ["topic_alpha", "topic_beta", "topic_gamma"]

    for target_index, target in enumerate(targets):
        target_time = base + timedelta(minutes=target_index * 12)
        for account_index, account_id in enumerate(accounts):
            event_id = f"campaign_{target_index:02d}_{account_index:02d}"
            variant = "hemen" if account_index % 3 else "şimdi"
            events.append(
                SocialEvent(
                    event_id=event_id,
                    account_id=account_id,
                    event_type=EventType.POST,
                    created_at=target_time + timedelta(seconds=account_index * 2),
                    text=f"Gündemi birlikte yükselt {variant} ortak çağrı {target}",
                    target_id=target,
                    urls=("https://example.test/common",),
                    hashtags=("OrtakCagri",),
                    synthetic=True,
                )
            )
            if target_index == 0 and account_index < 6:
                events.append(
                    SocialEvent(
                        event_id=f"delete_{event_id}",
                        account_id=account_id,
                        event_type=EventType.DELETE,
                        created_at=target_time + timedelta(minutes=4, seconds=account_index),
                        reference_event_id=event_id,
                        synthetic=True,
                    )
                )
    return sorted(events, key=lambda event: (event.created_at, event.event_id))


def organic_discussion() -> list[SocialEvent]:
    base = datetime(2025, 6, 15, 12, 0, tzinfo=UTC)
    texts = [
        "Maçın ikinci yarısında orta saha daha dengeli oynadı",
        "Bugünkü karşılaşmada kalecinin kurtarışı çok önemliydi",
        "Tribündeki atmosfer televizyondan bile hissediliyordu",
        "Genç oyuncuların süre alması gelecek adına umut verdi",
        "Teknik direktörün oyuncu değişikliği oyunun yönünü çevirdi",
        "Deplasman ekibi savunmada uzun süre direnç gösterdi",
        "Hakemin uzatma süresi kararı taraftarları şaşırttı",
        "Takımlar sahaya farklı dizilişlerle çıktı",
        "Maç sonu açıklamalarında fair play vurgusu yapıldı",
        "Yağmura rağmen stadyum tamamen doluydu",
        "İlk yarıdaki tempo ikinci yarıda belirgin biçimde arttı",
        "Puan tablosundaki rekabet son haftaya taşındı",
    ]
    events = [
        SocialEvent(
            event_id=f"organic_{index:02d}",
            account_id=f"organic_{index:02d}",
            event_type=EventType.POST,
            created_at=base + timedelta(minutes=index * 7),
            text=text,
            target_id="sports_event",
            synthetic=True,
        )
        for index, text in enumerate(texts)
    ]
    return events


def announced_campaign() -> list[SocialEvent]:
    """A transparent civic campaign that may look coordinated but is not covert."""
    base = datetime(2025, 6, 16, 8, 0, tzinfo=UTC)
    accounts = [f"volunteer_{index:02d}" for index in range(1, 7)]
    context = CoordinationContext(
        context_type=CoordinationContextType.PUBLIC_ANNOUNCEMENT,
        label="Duyurulmuş fidan dikme etkinliği",
        source_url="https://example.test/public-announcement",
        disclosure_id="announcement_tree_planting_2025_06_16",
    )
    return [
        SocialEvent(
            event_id=f"announced_{index:02d}",
            account_id=account_id,
            event_type=EventType.POST,
            created_at=base + timedelta(seconds=index * 12),
            text=(
                "Bugün saat 18.00'de duyurulan fidan dikme etkinliğine katılıyoruz "
                f"gönüllü mesajı {index}"
            ),
            target_id="announced_tree_planting_event",
            urls=("https://example.test/public-announcement",),
            hashtags=("BirlikteYesert",),
            coordination_context=context,
            synthetic=True,
        )
        for index, account_id in enumerate(accounts)
    ]


SCENARIOS: dict[str, Callable[[], list[SocialEvent]]] = {
    "announced-campaign": announced_campaign,
    "coordinated-campaign": coordinated_campaign,
    "organic-discussion": organic_discussion,
}


def load_scenario(name: str) -> list[SocialEvent]:
    try:
        factory = SCENARIOS[name]
    except KeyError as error:
        available = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario '{name}'; available scenarios: {available}") from error
    return factory()
