# Example 1
from engine import Rule

rule = Rule({'field': 'premium', 'operator': '>', 'value': 100e3})

assert rule.evaluate({'premium': 99e3}) is False
assert rule.evaluate({'premium': 101e3}) is True


# Example 2
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
