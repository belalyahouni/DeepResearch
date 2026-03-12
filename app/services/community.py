"""Community activity tracking service.

Provides a single helper to upsert community paper records.
Called by routers whenever a user directly interacts with a paper.

Interaction triggers (by design):
- GET /papers/{arxiv_id}        — direct lookup, clear reading intent
- POST /summarise with arxiv_id — highest intent, actively processing
- GET /papers/{arxiv_id}/related — engaged reader exploring further work

Search results are intentionally excluded: a paper appearing in many
search queries would inflate its count artificially without genuine engagement.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community_interaction import CommunityInteraction
from app.models.community_paper import CommunityPaper


async def track_interaction(arxiv_id: str, db: AsyncSession) -> None:
    """Upsert a CommunityPaper record and append a CommunityInteraction event.

    Silently absorbs any DB errors so a tracking failure never breaks the
    calling endpoint.
    """
    try:
        result = await db.execute(
            select(CommunityPaper).where(CommunityPaper.arxiv_id == arxiv_id)
        )
        community = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if community:
            community.interaction_count += 1
            community.last_interacted_at = now
        else:
            db.add(CommunityPaper(
                arxiv_id=arxiv_id,
                interaction_count=1,
                last_interacted_at=now,
            ))

        db.add(CommunityInteraction(arxiv_id=arxiv_id, interacted_at=now))

        await db.commit()
    except Exception:
        await db.rollback()
