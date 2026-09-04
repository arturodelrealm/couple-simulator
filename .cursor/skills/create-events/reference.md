# Action args (current handlers)

Not a ceiling. Missing effect → propose a new `{type, args}`; do not reshape the event. Do not implement until asked. Do not add event tests.

| type | args |
|------|------|
| `modify_stat` | `variable`, `delta` |
| `set_stat` | `variable`, `value` (absolute; compatibility sets both partners) |
| `set_event_var` | `variable`, `value` |
| `add_conversation` | `speaker`, `text_key` (`params` optional) |
| `add_timeline_entry` | `title_key`, `category` (`description_key` optional) |
| `advance_life_stage` | `to`: `youth\|adult\|elderly` |
| `end_game` | `reason` |
| `set_housing` | `place`, `type` (`apartment\|house`), `quality` (`bad\|ok\|excellent`) |
| `set_mascot` | `species`+`name`, or `mascot: null` |
| `set_tag` | `key` (no `/`), `value` (null removes) |
| `update_avatar` | `player` (`partner_a\|partner_b`), `attribute` (DiceBear key), `value` |

Paths: `state/{finances,age,compatibility,wellness,children,life_stage,relationship_status}`, `state/housing/{place,type,quality}`, `state/mascot`, `answers/{qid}`, `event_variables/{name}`, `flags/{has_mismatch,answers_match,match_count}`.

## Distributions

Used in `set_event_var` `value` (branch roll) or `modify_stat` `delta` (random amount). Full branching recipe: [SKILL.md § Probabilistic outcomes](SKILL.md#probabilistic-outcomes).

```json
{
  "distribution": {
    "kind": "uniform",
    "params": { "min": 1, "max": 100 }
  }
}
```

| kind | params | use |
|------|--------|-----|
| `uniform` | `min`, `max` (int) | Roll 1–100 for % thresholds; or random delta in range |
| `normal` | `median`, `std` | Gaussian delta around median |

Roll variable name is free (`illness_roll`, `caught_roll`, …). Outcomes compare `event_variables/{name}` with `lte` / `gt` against the threshold. Branches must cover the full range (e.g. `lte 50` + `gt 50`).
