# HANDOVER — AI Product Recommender

**Module owner:** Ubaid Ullah Farooqui (UF)
**Endpoint:** `GET /api/ai/recommendations` (Private)
**Status:** complete — Days 08, 09, 10

---

## For Talha — what to merge

Six files are mine. Copy them across as-is:

```
app/ai/recommender.py
app/ai/embeddings.py
app/services/ai_service.py
app/schemas/ai_schema.py
app/utils/constants.py
app/utils/seed_recommender_data.py
```

Three files are yours. Take only these lines from my copies:

**`app/api/v1/router.py`**
```python
from app.api.v1.endpoints import ai
api_router.include_router(ai.router)
```

**`app/main.py`** — a startup hook so the first shopper doesn't pay the index build
```python
from app.ai.recommender import recommender_service
recommender_service.warmup(force=True)
```

**`app/core/config.py`** — these fields on `Settings`, all namespaced so nothing collides
```
GROQ_API_KEY, GROQ_MODEL, GROQ_ENABLED
RECOMMENDER_DEFAULT_LIMIT, RECOMMENDER_MAX_LIMIT
RECOMMENDER_CACHE_TTL_SECONDS, TRENDING_WINDOW_DAYS
PRODUCT_ID_PREFIX, PRODUCT_ID_PAD
USE_SYNTHETIC_FALLBACK, SYNTHETIC_DATASET_PATH
```

`app/api/v1/endpoints/ai.py` is shared — my routes are in a marked block, the
other five AI routes have placeholder comments below it.

---

## One change I could not make myself

The route currently takes `userId` as a query parameter because auth was not
merged when I built it. It needs the JWT dependency:

```python
def get_recommendations(
    current_user = Depends(get_current_user),
    limit: int | None = Query(default=None, ge=1, le=20),
):
    payload = recommender_service.recommend(user_id=current_user.id, limit=limit)
```

Until that swap, the endpoint is effectively public and one shopper can read
another's recommendations by changing a number in the URL. Not a leak of
anything sensitive — product ids and reason strings only — but it should not
ship that way.

---

## Open question for the team

The documentation specifies `"productId": "P001"`, but `products.id` is a
`SERIAL` integer. I format ids as `P` + zero-padded 3, configurable via
`PRODUCT_ID_PREFIX` / `PRODUCT_ID_PAD` in `.env`.

**Sibgha and Talha need to agree on one of:**
- keep `P001` — frontend strips the prefix to look up the numeric id, or
- switch to raw integers — set `PRODUCT_ID_PREFIX=` and `PRODUCT_ID_PAD=1`

Either works without a code change. It just has to be decided before
integration testing.

---

## Deployment notes (Render)

The module reads from PostgreSQL when `DATABASE_URL` is set and the `products`
table has rows. Otherwise it falls back to a generated synthetic dataset.

**The build command must generate that dataset**, or a container with no
database starts with an empty catalogue:

```
pip install -r requirements.txt && python -m app.utils.seed_recommender_data
```

`data/synthetic_dataset.json` is gitignored — it is generated output, identical
every time from `RANDOM_SEED = 42`.

Leave `DATABASE_URL` **empty** rather than set to a placeholder. A wrong
hostname costs 3–8 seconds of DNS timeout on every cold start before the
fallback kicks in.

---

## How the module behaves

| Channel | Algorithm |
|---|---|
| `personalized` | Item-based collaborative filtering over a recency-decayed user-item matrix (orders, cart, wishlist) |
| `boughtTogether` | Cosine-normalised item co-occurrence from `orders.items`, anchored on the shopper's most recent purchase |
| `trending` | Recency-weighted purchase counts, rating as tie-break |
| cold start | TF-IDF content similarity over name + description + category + brand |

Fallback chain: collaborative filtering → content similarity → trending →
featured. **A channel is never empty and the endpoint never 500s on missing
data.** No LLM is called — recommendations are arithmetic over your own order
data, so there is nothing to hallucinate and no per-request cost.

Everything expensive is precomputed at warmup into an in-memory index,
refreshed on a 300s TTL. A request is dictionary lookups.

---

## Verification

```powershell
pytest -q                 # 17 unit tests — the similarity maths
python verify_day08.py    # 20 checks — the API contract
python verify_day09.py    # 19 checks — the algorithms
```

Postman: import `RRVDXB_Recommender.postman_collection.json`, set `base_url`,
run the collection. Six requests with assertions.

---

## What is not proven

The algorithms are verified correct against synthetic data containing
co-purchase bundles I planted deliberately. That demonstrates the maths works;
it is **not** evidence of recommendation quality against real shopper
behaviour, which nobody can claim until the platform has real orders.

When the shared database has real data, set `DATABASE_URL` and re-run both
verifier scripts. The PostgreSQL read path has been exercised against a real
server with the documented schema and returns results identical to the
synthetic path, so `orders.items` JSONB parsing is known to be correct.
