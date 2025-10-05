"""Stateless RNG helpers keyed by person_uid and a tag so draws are reproducible
independent of execution order.
"""
import numpy as _np


def _seed_from(person_uid: int, tag: str, year: int = 0) -> int:
    # Simple deterministic 64-bit seed from components
    h = (int(person_uid) & 0xFFFFFFFFFFFF) ^ (hash(tag) & 0xFFFFFFFFFFFF) ^ (year & 0xFFFF)
    return int(h & 0x7FFFFFFF)


def bernoulli(person_uids, p, tag: str, year: int = 0):
    # p can be scalar or array-like matching person_uids
    p_arr = _np.broadcast_to(p, len(person_uids))
    out = _np.zeros(len(person_uids), dtype=bool)
    for i, uid in enumerate(person_uids):
        seed = _seed_from(uid, tag, year)
        rng = _np.random.RandomState(seed)
        out[i] = rng.random_sample() < p_arr[i]
    return out


def normal(person_uids, mu_sigma_pairs, tag: str, year: int = 0):
    # mu_sigma_pairs is an iterable of (mu, sigma) for each uid
    out = _np.zeros(len(person_uids), dtype=_np.float64)
    for i, uid in enumerate(person_uids):
        mu, sigma = mu_sigma_pairs[i]
        seed = _seed_from(uid, tag, year)
        rng = _np.random.RandomState(seed)
        out[i] = rng.normal(mu, sigma)
    return out


def poisson(person_uids, lam_arr, tag: str, year: int = 0):
    out = _np.zeros(len(person_uids), dtype=int)
    for i, uid in enumerate(person_uids):
        seed = _seed_from(uid, tag, year)
        rng = _np.random.RandomState(seed)
        out[i] = rng.poisson(lam_arr[i])
    return out


def categorical(person_uids, categories, probs=None, tag: str = "cat", year: int = 0):
    """Stateless categorical draw per person. Returns integer indices into categories.
    - categories: list-like of choices (values are not used, only indices returned)
    - probs: probability vector (will be broadcasted to length of person_uids)
    """
    k = len(categories)
    out = _np.zeros(len(person_uids), dtype=int)
    # If probs is None, uniform
    if probs is None:
        probs = _np.ones(k) / k
    probs = _np.asarray(probs)
    for i, uid in enumerate(person_uids):
        seed = _seed_from(uid, tag, year)
        rng = _np.random.RandomState(seed)
        out[i] = rng.choice(k, p=probs)
    return out
