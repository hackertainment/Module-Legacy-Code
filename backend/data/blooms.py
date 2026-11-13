import datetime

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from data.connection import db_cursor
from data.users import User


@dataclass
class Bloom:
    id: int
    sender: User
    content: str
    sent_timestamp: datetime.datetime
    count: int
    rebloomer: User


def add_bloom(*, sender: User, content: str) -> Bloom:
    hashtags = [word[1:] for word in content.split(" ") if word.startswith("#")]

    now = datetime.datetime.now(tz=datetime.UTC)
    bloom_id = int(now.timestamp() * 1000000)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp) VALUES (%(bloom_id)s, %(sender_id)s, %(content)s, %(timestamp)s)",
            dict(
                bloom_id=bloom_id,
                sender_id=sender.id,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC),
            ),
        )
        for hashtag in hashtags:
            cur.execute(
                "INSERT INTO hashtags (hashtag, bloom_id) VALUES (%(hashtag)s, %(bloom_id)s)",
                dict(hashtag=hashtag, bloom_id=bloom_id),
            )


def get_blooms_for_user(
    username: str, *, before: Optional[int] = None, limit: Optional[int] = None
) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs = {
            "sender_username": username,
        }
        if before is not None:
            before_clause = "AND send_timestamp < %(before_limit)s"
            kwargs["before_limit"] = before
        else:
            before_clause = ""

        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp, COALESCE(t.rebloom_count, 0) AS rebloom_count
            FROM
              blooms INNER JOIN users ON users.id = blooms.sender_id
            LEFT OUTER JOIN (
              SELECT bloom_id, COUNT(*) AS rebloom_count FROM reblooms GROUP BY bloom_id
            ) t ON t.bloom_id = blooms.id
            WHERE
              username = %(sender_username)s
              {before_clause}
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp, rebloom_count = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                    count=rebloom_count,
                    rebloomer=None,
                )
            )
    return blooms


def get_reblooms_for_user(
    username: str, *, before: Optional[int] = None, limit: Optional[int] = None
) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs = {
            "rebloomer_username": username,
        }
        if before is not None:
            before_clause = "AND rebloom_timestamp < %(before_limit)s"
            kwargs["before_limit"] = before
        else:
            before_clause = ""

        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""SELECT
              blooms.id, senders.username, blooms.content, rebloom_timestamp, t.rebloom_count, rebloomers.username
            FROM
              reblooms INNER JOIN blooms ON blooms.id = reblooms.bloom_id
                       INNER JOIN users AS senders ON senders.id = blooms.sender_id
                       INNER JOIN users AS rebloomers ON rebloomers.id = reblooms.rebloomer_id
            LEFT OUTER JOIN (
              SELECT bloom_id, COUNT(*) AS rebloom_count FROM reblooms GROUP BY bloom_id
            ) t ON t.bloom_id = reblooms.bloom_id
            WHERE
              rebloomers.username = %(rebloomer_username)s
              {before_clause}
            ORDER BY rebloom_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp, rebloom_count, rebloomer_username = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                    count=rebloom_count,
                    rebloomer=rebloomer_username,
                )
            )
    return blooms


def get_bloom(bloom_id: int) -> Optional[Bloom]:
    with db_cursor() as cur:
        select_field = ", COALESCE(t.rebloom_count, 0) AS rebloom_count"
        left_join_clause = "LEFT OUTER JOIN (SELECT bloom_id, COUNT(*) AS rebloom_count FROM reblooms GROUP BY bloom_id) t ON t.bloom_id = blooms.id"
        cur.execute(
            f"SELECT blooms.id, users.username, content, send_timestamp{select_field} FROM blooms INNER JOIN users ON users.id = blooms.sender_id {left_join_clause} WHERE blooms.id = %s",
            (bloom_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        bloom_id, sender_username, content, timestamp, rebloom_count = row
        return Bloom(
            id=bloom_id,
            sender=sender_username,
            content=content,
            sent_timestamp=timestamp,
            count=rebloom_count,
            rebloomer=None,
        )


def get_blooms_with_hashtag(
    hashtag_without_leading_hash: str, *, limit: int = None
) -> List[Bloom]:
    kwargs = {
        "hashtag_without_leading_hash": hashtag_without_leading_hash,
    }
    limit_clause = make_limit_clause(limit, kwargs)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp, COALESCE(t.rebloom_count, 0) AS rebloom_count
            FROM
              blooms INNER JOIN hashtags ON blooms.id = hashtags.bloom_id INNER JOIN users ON blooms.sender_id = users.id
            LEFT OUTER JOIN (
              SELECT bloom_id, COUNT(*) AS rebloom_count FROM reblooms GROUP BY bloom_id
            ) t ON t.bloom_id = blooms.id
            WHERE
              hashtag = %(hashtag_without_leading_hash)s
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp, rebloom_count = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                    count=rebloom_count,
                    rebloomer=None,
                )
            )
    return blooms


def make_limit_clause(limit: Optional[int], kwargs: Dict[Any, Any]) -> str:
    if limit is not None:
        limit_clause = "LIMIT %(limit)s"
        kwargs["limit"] = limit
    else:
        limit_clause = ""
    return limit_clause
