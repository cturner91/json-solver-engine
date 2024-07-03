# Rules Engine

As part of a technical challenge for an interview, I was tasked with creating a flexible rules-solving engine. The requirements are given below:

## Requirements

These rules need to be configurable and variable in several ways:
- The number of comparisons
- The variables referenced (e.g. replacing `credit_rating` with something else)
- The constant values being compared against
- The operators being used (e.g. greater than, less than, equals)
- The structure of the boolean composition (i.e where AND/OR/etc are, and where the parentheses are)

## CT Assumptions:

* Payload of data is a single-level dict i.e. no nested fields.
* All fields required for each evaluation are present in the payload - code intentionally throws an error if this is not the case.

## How to use:

Import from `engine.py` and configure a rule using the spec. There are two Rule-Spec formats acceptable in the JSON when creating rules:

1. Bool-ops i.e. '**AND**' and '**OR**'. If this key is in the JSON, the nested value must be a **list** of more rule-specs e.g. `{'AND': [spec1, spec2, ...]}`

2. Standard rule-spec -> a `dict` with `field`, `operator`, and `value` all specified e.g. `{"field": "credit_score", "operator": ">", "value": 90}`

## Examples:

Basic example: Trigger if the client's premium is above 100k

```python
from engine import Rule

rule = Rule({'field': 'premium', 'operator': '>', 'value': 100e3})

assert rule.evaluate({'premium': 99e3}) is False
assert rule.evaluate({'premium': 101e3}) is True
```

More sophisticated example: Trigger if the client's premium is above 100k AND either their flood risk is above 90% or their credit score is below 100:

```python
from engine import Rule

rule = Rule({
    'AND': [
        {'field': 'premium', 'operator': '>', 'value': 100e3},
        {'OR': [
            {'field': 'flood_risk_pc', 'operator': '>', 'value': 90},
            {'field': 'credit_score', 'operator': '<', 'value': 100}
        ]},
    ]
})

assert rule.evaluate({'premium': 99e3, 'flood_risk_pc': 50, 'credit_score': 500}) is False
assert rule.evaluate({'premium': 101e3, 'flood_risk_pc': 95, 'credit_score': 500}) is True
assert rule.evaluate({'premium': 101e3, 'flood_risk_pc': 50, 'credit_score': 50}) is True
```

## To run tests:

The tests can be run using `python -m unittest tests` in the directory of this README. Results should be:

```python
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
```

## Areas for improvement

* Type coercion - Currently, we can get errors if the payload type does not match the defined Rule type e.g. comparing `'101e3' > 100e3` will generate an exception.

* Nested payloads - It's unlikely that the data we are working with is perfectly flat dictionaries. Therefore, we should consider some way to extract nested values (or maybe this flattening is the responsibility of another component in the system?).

* Null-handling - currently, if an expected field is not present, we will raise an exception. This probably isn't good enough for a production system. We should think about how to handle such scenarios and what to do about them.

## Disclaimer:

This was put together in about 48 hours for a technical challenge for an interview. I am aware it could be improved in many ways, but it works at a basic level, and it was an interesting and fun project.
