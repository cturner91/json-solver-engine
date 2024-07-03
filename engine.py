import json
from typing import Any, Dict, Callable, Union


'''
Notes: I want it to be fully JSON interoperable. 
I should be able to configure rules and payloads in pure JSON, with no code.
If we can make this work, then we should be able to fully configure via an API 👀
'''


def _ensure_dict(payload: Union[dict, str]):
    '''Simple utility method so I don't need to worry about input type in the other classes'''
    if isinstance(payload, dict):
        return payload
    elif isinstance(payload, str):
        return json.loads(payload)  # let errors raise
    raise TypeError(f'Payload type {type(payload)} not able to convert to dict')


class Comparator:
    '''A class that defines how to perform the logical evaluation
    This class configures the logical expression to be evaluated, and can then be evaluated against
    a custom payload via the .evaluate() method'''

    # class attribute to define comparator functions
    funcs: Dict[str, Callable] = {
        '=': lambda x, y: x == y,
        '==': lambda x, y: x == y,
        '!=': lambda x, y: x != y,
        '<>': lambda x, y: x != y,
        '>': lambda x, y: x > y,
        '>=': lambda x, y: x >= y,
        '<': lambda x, y: x < y,
        '<=': lambda x, y: x <= y,

        # Turns out this is a very flexible solution... how far can I push it?
        'in': lambda x, y: x in y,
        '===': lambda x, y: type(x) is type(y) and x == y,
    }

    def __init__(self, field: str, operator: str, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def evaluate(self, payload: Union[dict, str]) -> bool:
        payload = _ensure_dict(payload)

        # don't use .get() -> I WANT it to raise an exception if we pass a bad operator/field. 
        # I figure this is safer than providing a bad value to the application/client.
        field_value = payload[self.field]
        func = self.funcs[self.operator]
        return func(field_value, self.value)


class Rule:

    _BOOL_OPERATORS: Dict[str, Callable] = {
        'AND': lambda values: all(values),
        'OR': lambda values: any(values),
    }
    
    def __init__(self, rule: Union[dict, str], skip_validation: bool = False):
        '''skip_validation is becase constructor can be called recursively.
        We don't always need to validate every time. Let's save some CPU cycles.'''

        rule = _ensure_dict(rule)

        if not skip_validation:
            self._validate_rule_json(rule)
        self.rule = rule

    def _validate_rule_json(self, rule: dict):
        '''Ensure that the given rule is a valid rule-spec.

        Two allowable formats:
        * {'<bool-op>': [*list-of-specs]}
        * {'field': '<field_name>', 'operator': '<operator>', 'constant': <constant>}

        <bool-op> must be 'AND' or 'OR'
        '''
        for bool_op in self._BOOL_OPERATORS:
            if bool_op in rule:
                for subrule in rule[bool_op]:
                    self._validate_rule_json(subrule)

                # it was a bool-op, and has all been validated OK
                return
            
        # is not a bool-op, must adhere to comparator-spec
        for required_field in ('field', 'operator', 'value'):
            if required_field not in rule:
                # it could be heavily nested, so try and give some relevant info if it does fail
                raise KeyError(f'Required field "{required_field}" not in rule-spec. Offending spec:\n\n{json.dumps(rule)}')

        # otherwise - all looks good!

    def evaluate(self, payload: dict):

        # as with validation - if we have a bool-op, then evaluate it for all sub-elements
        for bool_op in self._BOOL_OPERATORS:
            if bool_op in self.rule:
                results = [
                    Rule(subrule, skip_validation=True).evaluate(payload) 
                    for subrule in self.rule[bool_op]
                ]
                return self._BOOL_OPERATORS[bool_op](results)
            
        # not a bool-op - evaluate normally
        return Comparator(**self.rule).evaluate(payload)
