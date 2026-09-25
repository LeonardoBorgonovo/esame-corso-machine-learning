"""shared/pagination.py — platform-standard pagination helpers."""
from __future__ import annotations
from errors import ValidationError


def parse_pagination(args) -> tuple[int, int]:
    """Parse page / page_size from request query args.

    Returns (page, page_size). Raises ValidationError on invalid values.
    """
    try:
        page = int(args.get("page", 1))
    except (ValueError, TypeError):
        raise ValidationError("'page' must be a positive integer")
    try:
        page_size = int(args.get("page_size", 20))
    except (ValueError, TypeError):
        raise ValidationError("'page_size' must be a positive integer")

    if page < 1:
        raise ValidationError("'page' must be >= 1")
    if page_size < 1 or page_size > 100:
        raise ValidationError("'page_size' must be between 1 and 100")

    return page, page_size


def paginate(items: list, page: int, page_size: int) -> dict:
    """Slice items and return the platform-standard paginated envelope."""
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
