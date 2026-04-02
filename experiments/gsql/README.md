# Alternate GSQL sources

These queries are **not** referenced by the Flask API allowlist. Install on your TigerGraph instance only if you need them:

- `chintu_causal_explosion.gsql` — non-viz variant of causal expansion
- `chintu_entity_influence_map.gsql` — entity-centric influence view

Use the same REST installer as production queries, pointing at this directory:

`python scripts/install_chintu_query.py experiments/gsql/<file>.gsql`
