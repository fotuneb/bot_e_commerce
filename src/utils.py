import logging
import random
import string
from typing import Final

logger = logging.getLogger(__name__)


def gen_order_number(prefix: str = 'ORD') -> str:
    """Generate a short unique order number.

    The function returns a string like "ORD-1A2B3C" where the suffix is 6
    random alphanumeric characters.

    Args:
        prefix: Optional prefix for the order number.

    Returns:
        A string order number.
    """
    ALPHANUM: Final = string.ascii_uppercase + string.digits
    rnd = ''.join(random.choices(ALPHANUM, k=6))
    order = f"{prefix}-{rnd}"
    logger.debug('Generated order number: %s', order)
    return order

