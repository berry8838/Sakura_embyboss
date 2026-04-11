import asyncio
from collections import OrderedDict

_MAX_LOCKS = 1024
_user_locks: OrderedDict[int, asyncio.Lock] = OrderedDict()


def get_user_lock(user_id: int) -> asyncio.Lock:
    lock = _user_locks.get(user_id)
    if lock is not None:
        _user_locks.move_to_end(user_id)
        return lock
    lock = asyncio.Lock()
    _user_locks[user_id] = lock
    if len(_user_locks) > _MAX_LOCKS:
        to_evict = [
            uid for uid, lk in _user_locks.items()
            if not lk.locked() and uid != user_id
        ]
        for uid in to_evict[:len(_user_locks) - _MAX_LOCKS]:
            _user_locks.pop(uid, None)
    return lock
