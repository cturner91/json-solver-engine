from json.decoder import JSONDecodeError
import unittest

from engine import Rule, Comparator, _ensure_dict


'''Note to self: I have got to learn how to use pytest one day...'''


class ComparatorTest(unittest.TestCase):


    def test_different_values_different_operators(self):
        # Cannot be exhaustive here, too many combinations. Pick a range of everything.

        # test all operators 
        for payload_value, operator, compare_value, expected_result in (
            (75, '=', 75, True),
            (75, '==', 75, True),
            (75, '>', 75, False),
            (75, '>=', 75, True),
            (72, '<', 75, True),
            (77, '<', 75, False),
            (77, '>', 75, True),
            (72, '>=', 75, False),
            (75, '!=', 75, False),
            (75, '<>', 75, False),

            # new operators - strong typing and IN
            (75.0, '=', 75, True),
            (75.0, '===', 75, False),
            (75, 'in', [73, 75, 77], True),
            (79, 'in', [73, 75, 77], False),
        ):
            with self.subTest(f'{payload_value} {operator} {compare_value}'):
                comparator = Comparator(
                    field='risk_score',
                    operator=operator,
                    value=compare_value,
                )
                result = comparator.evaluate({'risk_score': payload_value})
                self.assertTrue(result is expected_result)

    def test_bad_operator(self):
        comparator = Comparator(
            field='risk_score',
            operator='dfg',
            value=75,
        )
        with self.assertRaises(KeyError):
            comparator.evaluate({'risk_score': 75})

    def test_bad_field_name(self):
        comparator = Comparator(
            field='risk_score',
            operator='dfg',
            value=75,
        )
        with self.assertRaises(KeyError):
            comparator.evaluate({'bad_key': 75})


class EnsureDictTest(unittest.TestCase):

    def test_dict(self):
        data = {'field1': 'value1', 'field2': 2}
        self.assertDictEqual(_ensure_dict(data), data)

    def test_string(self):
        data = '{"field1": "value1", "field2": 2}'
        self.assertDictEqual(_ensure_dict(data), {'field1': 'value1', 'field2': 2})

    def test_bad_string(self):
        data = "abcdefg"
        with self.assertRaises(JSONDecodeError):
            _ensure_dict(data)

    def test_bad_type(self):
        with self.assertRaises(TypeError):
            _ensure_dict(1)


class RuleTest(unittest.TestCase):

    def setUp(self):
        self.valid_comparator_spec = {
            'field': 'risk_score',
            'operator': '>=', 
            'value': 75,
        }

    def test_construction_single_bad(self):
        rule_json = {
            'field': 'risk_score',
            'operator': '>=', 
            'value': 75,
        }
        for del_key in ('field', 'operator', 'value'):
            broken_json = {**rule_json}
            del broken_json[del_key]

            with self.assertRaises(KeyError):
                Rule(broken_json)

    def test_construction_single_bool_op(self):
        rule_json = {
            'AND': [self.valid_comparator_spec] * 4
        }
        rule = Rule(rule_json)
        self.assertEqual(rule.rule, rule_json)

    def test_construction_nested_bool_op(self):
        rule_json = {
            'AND': [
                {'OR': [self.valid_comparator_spec] * 2},
                {'AND': [self.valid_comparator_spec] * 3},
            ]
        }
        rule = Rule(rule_json)
        self.assertEqual(rule.rule, rule_json)     

    def test_evaluation_single(self):
        rule_json = {**self.valid_comparator_spec}
        rule = Rule(rule_json)
        self.assertTrue(rule.evaluate({'risk_score': 75}))
        self.assertFalse(rule.evaluate({'risk_score': 74}))

    def test_evaluation_AND(self):
        rule_json = {'AND': [{**self.valid_comparator_spec}]*2}
        rule = Rule(rule_json)
        self.assertTrue(rule.evaluate({'risk_score': 75}))
        self.assertFalse(rule.evaluate({'risk_score': 74}))

    def test_evaluation_OR(self):
        rule_json = {'OR': [{**self.valid_comparator_spec}]*2}
        rule = Rule(rule_json)
        self.assertTrue(rule.evaluate({'risk_score': 75}))
        self.assertFalse(rule.evaluate({'risk_score': 74}))

    def test_evaluation_nested_logicals(self):
        # different from test_construction_nested_bool_op, using OR rather than AND
        rule_json = {
            'OR': [
                {'OR': [self.valid_comparator_spec] * 2},
                {'AND': [self.valid_comparator_spec] * 3},
            ]
        }
        rule = Rule(rule_json)
        self.assertTrue(rule.evaluate({'risk_score': 75}))
        self.assertFalse(rule.evaluate({'risk_score': 74}))

    def test_nested_with_multiple_payload_fields(self):
        # Create a tricky rule. This might be how requirements from through from Customer team:
        # If customer premium is at or above 10k, trigger
        # if customer flood risk is above 90% and their last name is 'smith', trigger
        # if customer is between 175 and 185 centimetres tall, trigger
        # if customer is below 150 or above 200 centimetres tall, trigger
        rule_json = {
            'OR': [
                {
                    'field': 'premium',
                    'operator': '>=', 
                    'value': 10e3,
                },
                {'AND': [
                    {
                        'field': 'flood_risk_pc',
                        'operator': '>=', 
                        'value': 90,
                    },
                    {
                        'field': 'last_name',
                        'operator': '=', 
                        'value': 'smith',
                    },
                ]},
                {'AND': [
                    {
                        'field': 'height',
                        'operator': '>=', 
                        'value': 175,
                    },
                    {
                        'field': 'height',
                        'operator': '<=', 
                        'value': 185,
                    },
                ]},
                {'OR': [
                    {
                        'field': 'height',
                        'operator': '<', 
                        'value': 150,
                    },
                    {
                        'field': 'height',
                        'operator': '>', 
                        'value': 200,
                    },
                ]},
            ]
        }
        rule = Rule(rule_json)
        no_trigger = {
            'premium': 1000,
            'flood_risk_pc': 80,
            'last_name': 'jones',
            'height': 160,
        }
        with self.subTest('Default payload should not trigger'):
            self.assertFalse(rule.evaluate(no_trigger))

        with self.subTest('Premium too high'):
            self.assertTrue(rule.evaluate({**no_trigger, 'premium': 10e3}))

        with self.subTest('Triggers for flood risk and last name'):
            self.assertTrue(rule.evaluate({**no_trigger, 'flood_risk_pc': 90, 'last_name': 'smith'}))

        with self.subTest('Last name is smith but should not trigger because flood risk is too low'):
            self.assertFalse(rule.evaluate({**no_trigger, 'flood_risk_pc': 89, 'last_name': 'smith'}))

        with self.subTest('Should trigger for being below 150cm'):
            self.assertTrue(rule.evaluate({**no_trigger, 'height': 149}))

        with self.subTest('Should not trigger on height'):
            self.assertFalse(rule.evaluate({**no_trigger, 'height': 165}))

        with self.subTest('Should trigger for being between 175 and 185 cm'):
            self.assertTrue(rule.evaluate({**no_trigger, 'height': 180}))

        with self.subTest('Should not trigger on height'):
            self.assertFalse(rule.evaluate({**no_trigger, 'height': 195}))

        with self.subTest('Should trigger for being above 200cm'):
            self.assertTrue(rule.evaluate({**no_trigger, 'height': 201}))


if __name__ == '__main__':
    unittest.main()
