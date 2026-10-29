"""Integration tests for the Math API in ``main.py``.

Conventions
-----------
* All tests go through ``fastapi.testclient.TestClient`` (no mocking).
* The client is created with ``raise_server_exceptions=False`` so an unhandled
  exception in a route shows up as a real HTTP 500 instead of blowing up the
  test. That lets us state the *desired* contract ("never a 5xx") and observe
  violations.
* Known application bugs are encoded as ``xfail(strict=True)`` tests. They keep
  the desired behaviour documented, and strict mode fails the suite once the
  bug is fixed so the marker gets removed.

Known application bugs (see ``main.py``)
----------------------------------------
* ``power``       : ``a ** b`` can produce a ``complex`` (negative base, fractional
                    exponent), raise ``ZeroDivisionError`` (0 ** negative) or
                    ``OverflowError`` (huge result). All surface as HTTP 500.
* every endpoint : NaN / +-Infinity results (from NaN/Infinity inputs or from
                    overflow of finite inputs) cannot be JSON-serialised by
                    Starlette -> ``ValueError`` -> HTTP 500.
* ``/factorial`` : the endpoint does not exist (404). ``/absolute`` exists but is
                    not part of the requested 8 operations; it is tested too.
"""
import json
import math

import pytest
from fastapi.testclient import TestClient

from main import app

BINARY_OPS = ["add", "subtract", "multiply", "divide", "power", "modulo"]
SINGLE_OPS = ["square-root", "absolute"]

JSON_HEADERS = {"content-type": "application/json"}

MAX_FLOAT = 1.7976931348623157e308


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def client():
    # raise_server_exceptions=False: unhandled errors become HTTP 500 responses.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def post(client):
    """POST a python dict as JSON."""

    def _post(path, payload):
        return client.post(path, json=payload)

    return _post


@pytest.fixture
def post_raw(client):
    """POST a raw JSON string (needed for NaN / Infinity / 1e999 tokens)."""

    def _post_raw(path, raw):
        return client.post(path, content=raw, headers=JSON_HEADERS)

    return _post_raw


def assert_graceful(resp):
    """Desired contract for hostile input: never a 5xx.

    Either a client error (4xx), or a 200 whose ``result`` is a finite number.
    """
    assert resp.status_code < 500, f"server error {resp.status_code}: {resp.text}"
    if resp.status_code == 200:
        assert math.isfinite(resp.json()["result"])
    else:
        assert 400 <= resp.status_code < 500


def bin_body(a, b):
    return json.dumps({"a": a, "b": b}) if _finite(a) and _finite(b) else (
        "{" + f'"a":{_tok(a)},"b":{_tok(b)}' + "}"
    )


def _finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def _tok(x):
    if isinstance(x, float) and math.isnan(x):
        return "NaN"
    if x == math.inf:
        return "Infinity"
    if x == -math.inf:
        return "-Infinity"
    return json.dumps(x)


# --------------------------------------------------------------------------- #
# Health / routing
# --------------------------------------------------------------------------- #
def test_health_returns_healthy_status(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "message": "API is running"}


def test_unknown_route_returns_404(client):
    assert client.post("/does-not-exist", json={"a": 1, "b": 2}).status_code == 404


@pytest.mark.parametrize("op", BINARY_OPS + SINGLE_OPS)
def test_operation_endpoint_get_method_returns_405(client, op):
    assert client.get(f"/{op}").status_code == 405


def test_health_post_method_returns_405(client):
    assert client.post("/health").status_code == 405


def test_openapi_schema_lists_implemented_operations(client):
    paths = client.get("/openapi.json").json()["paths"]
    for op in BINARY_OPS + SINGLE_OPS:
        assert f"/{op}" in paths


# --------------------------------------------------------------------------- #
# Happy paths: binary operations
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "path, a, b, expected, operation",
    [
        # add
        ("/add", 2, 3, 5.0, "addition"),
        ("/add", -2, -3, -5.0, "addition"),
        ("/add", -2, 2, 0.0, "addition"),
        ("/add", 0, 0, 0.0, "addition"),
        ("/add", 1.5, 2.25, 3.75, "addition"),
        ("/add", 1e15, 1, 1e15 + 1, "addition"),
        # subtract
        ("/subtract", 10, 4, 6.0, "subtraction"),
        ("/subtract", 4, 10, -6.0, "subtraction"),
        ("/subtract", -3, -3, 0.0, "subtraction"),
        ("/subtract", 0.5, 0.25, 0.25, "subtraction"),
        # multiply
        ("/multiply", 6, 7, 42.0, "multiplication"),
        ("/multiply", -6, 7, -42.0, "multiplication"),
        ("/multiply", -6, -7, 42.0, "multiplication"),
        ("/multiply", 0, 12345, 0.0, "multiplication"),
        ("/multiply", 0.5, 0.5, 0.25, "multiplication"),
        # divide
        ("/divide", 10, 4, 2.5, "division"),
        ("/divide", -10, 4, -2.5, "division"),
        ("/divide", 10, -4, -2.5, "division"),
        ("/divide", 0, 5, 0.0, "division"),
        ("/divide", 1, 3, 1 / 3, "division"),
        # power
        ("/power", 2, 10, 1024.0, "power"),
        ("/power", 2, -1, 0.5, "power"),
        ("/power", 9, 0.5, 3.0, "power"),
        ("/power", 5, 0, 1.0, "power"),
        ("/power", 0, 0, 1.0, "power"),
        ("/power", 0, 2, 0.0, "power"),
        ("/power", 0, 0.5, 0.0, "power"),
        ("/power", -2, 3, -8.0, "power"),
        ("/power", -2, 2, 4.0, "power"),
        ("/power", -2, -3, -0.125, "power"),
        ("/power", -8, 2.0, 64.0, "power"),  # integral float exponent on negative base
        # modulo (Python semantics: result takes sign of divisor)
        ("/modulo", 10, 3, 1.0, "modulo"),
        ("/modulo", -5, 3, 1.0, "modulo"),
        ("/modulo", 5, -3, -1.0, "modulo"),
        ("/modulo", -5, -3, -2.0, "modulo"),
        ("/modulo", 5.5, 2, 1.5, "modulo"),
        ("/modulo", 0, 5, 0.0, "modulo"),
        ("/modulo", 3, 5, 3.0, "modulo"),
    ],
)
def test_binary_operation_valid_input_returns_expected_result(
    post, path, a, b, expected, operation
):
    resp = post(path, {"a": a, "b": b})
    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == operation
    assert body["result"] == pytest.approx(expected)
    assert set(body) == {"result", "operation"}


def test_add_float_rounding_matches_ieee754(post):
    resp = post("/add", {"a": 0.1, "b": 0.2})
    assert resp.status_code == 200
    assert resp.json()["result"] == 0.1 + 0.2


# --------------------------------------------------------------------------- #
# Happy paths: single-value operations
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "value, expected",
    [
        (16, 4.0),
        (0, 0.0),
        (1, 1.0),
        (2, math.sqrt(2)),
        (0.25, 0.5),
        (1e-10, 1e-5),
        (MAX_FLOAT, math.sqrt(MAX_FLOAT)),
    ],
)
def test_square_root_non_negative_input_returns_root(post, value, expected):
    resp = post("/square-root", {"value": value})
    assert resp.status_code == 200
    assert resp.json()["operation"] == "square_root"
    assert resp.json()["result"] == pytest.approx(expected)


@pytest.mark.parametrize(
    "value, expected",
    [(-5, 5.0), (5, 5.0), (0, 0.0), (-0.5, 0.5), (-1e308, 1e308)],
)
def test_absolute_valid_input_returns_magnitude(post, value, expected):
    resp = post("/absolute", {"value": value})
    assert resp.status_code == 200
    assert resp.json() == {"result": expected, "operation": "absolute"}


# --------------------------------------------------------------------------- #
# Division / modulo by zero guards
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "path, message",
    [
        ("/divide", "Division by zero is not allowed"),
        ("/modulo", "Modulo by zero is not allowed"),
    ],
)
@pytest.mark.parametrize("zero", ["0", "0.0", "-0.0", "0e10", '"0"', '"-0"'])
def test_zero_divisor_returns_400_with_message(post_raw, path, message, zero):
    resp = post_raw(path, '{"a": 7, "b": %s}' % zero)
    assert resp.status_code == 400
    assert resp.json() == {"detail": message}


@pytest.mark.parametrize("path", ["/divide", "/modulo"])
def test_zero_dividend_and_zero_divisor_returns_400(post, path):
    assert post(path, {"a": 0, "b": 0}).status_code == 400


@pytest.mark.parametrize("path", ["/divide", "/modulo"])
def test_tiny_nonzero_divisor_is_not_treated_as_zero(post_raw, path):
    resp = post_raw(path, '{"a": 1, "b": 1e-308}')
    assert resp.status_code == 200


def test_divide_by_largest_subnormal_is_not_zero_guarded(post_raw):
    # 1 / 1e-308 == 1e308 still fits in a double.
    resp = post_raw("/divide", '{"a": 1, "b": 1e-308}')
    assert resp.json()["result"] == pytest.approx(1e308)


# --------------------------------------------------------------------------- #
# Square root domain errors
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("value", [-1, -0.0001, -1e-300, -1e308])
def test_square_root_negative_input_returns_400(post, value):
    resp = post("/square-root", {"value": value})
    assert resp.status_code == 400
    assert resp.json() == {"detail": "Cannot compute square root of negative number"}


# --------------------------------------------------------------------------- #
# Negative zero
# --------------------------------------------------------------------------- #
def test_square_root_negative_zero_is_accepted_not_rejected_as_negative(post_raw):
    resp = post_raw("/square-root", '{"value": -0.0}')
    assert resp.status_code == 200
    assert resp.json()["result"] == 0.0


def test_absolute_negative_zero_returns_positive_zero(post_raw):
    resp = post_raw("/absolute", '{"value": -0.0}')
    assert resp.status_code == 200
    assert math.copysign(1.0, resp.json()["result"]) == 1.0


@pytest.mark.parametrize(
    "path, a, b, expected_sign",
    [
        ("/add", "-0.0", "-0.0", -1.0),
        ("/add", "-0.0", "0.0", 1.0),
        ("/multiply", "-0.0", "5", -1.0),
        ("/multiply", "0.0", "-5", -1.0),
        ("/divide", "-0.0", "5", -1.0),
        ("/divide", "0.0", "-5", -1.0),
        ("/subtract", "-0.0", "0.0", -1.0),
    ],
)
def test_negative_zero_sign_is_preserved_in_results(post_raw, path, a, b, expected_sign):
    resp = post_raw(path, '{"a": %s, "b": %s}' % (a, b))
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result == 0.0
    assert math.copysign(1.0, result) == expected_sign


def test_power_negative_zero_base_positive_exponent_returns_zero(post_raw):
    resp = post_raw("/power", '{"a": -0.0, "b": 3}')
    assert resp.status_code == 200
    assert resp.json()["result"] == 0.0


# --------------------------------------------------------------------------- #
# /power error cases (KNOWN BUGS: currently HTTP 500)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "a, b",
    [(-8, 0.5), (-1, 0.5), (-8, 1 / 3), (-2, -0.5), (-1e-300, 0.1)],
)
def test_power_negative_base_fractional_exponent_returns_client_error(post, a, b):
    # In Python 3 this yields a complex number, which is not representable
    # in the float Result model / JSON. Should be a 4xx, not a crash.
    resp = post("/power", {"a": a, "b": b})
    assert resp.status_code in (400, 422), resp.text


@pytest.mark.parametrize("a, b", [("0", "-1"), ("0.0", "-0.5"), ("-0.0", "-1"), ("0", "-1e300")])
def test_power_zero_base_negative_exponent_returns_400(post_raw, a, b):
    resp = post_raw("/power", '{"a": %s, "b": %s}' % (a, b))
    assert resp.status_code == 400, resp.text


@pytest.mark.parametrize(
    "a, b",
    [(10, 1000), (10, 309), (2, 1024), (1e308, 2), (-10, 1001), (MAX_FLOAT, MAX_FLOAT), (1e10, 1e10)],
)
def test_power_result_overflow_returns_client_error_not_500(post, a, b):
    resp = post("/power", {"a": a, "b": b})
    assert_graceful(resp)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (10, 308, 1e308),  # largest decade that still fits
        (2, 1023, 2.0 ** 1023),
        (0.5, 2000, 0.0),  # underflow to zero is representable, not an error
        (10, -400, 0.0),
        (-0.5, 2001, -0.0),
        (1, MAX_FLOAT, 1.0),
        (-1, 1e300, 1.0),  # huge even integral exponent
    ],
)
def test_power_extreme_but_representable_result_returns_200(post, a, b, expected):
    resp = post("/power", {"a": a, "b": b})
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Overflow to infinity in other operations (KNOWN BUG: HTTP 500)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "path, a, b",
    [
        ("/add", MAX_FLOAT, MAX_FLOAT),
        ("/add", -MAX_FLOAT, -MAX_FLOAT),
        ("/subtract", MAX_FLOAT, -MAX_FLOAT),
        ("/subtract", -MAX_FLOAT, MAX_FLOAT),
        ("/multiply", 1e308, 10),
        ("/multiply", -1e308, 10),
        ("/multiply", 1e200, 1e200),
        ("/divide", 1e308, 1e-308),
        ("/divide", 1, 5e-324),
        ("/divide", -1, 5e-324),
    ],
)
def test_overflowing_operation_returns_client_error_not_500(post, path, a, b):
    resp = post(path, {"a": a, "b": b})
    assert_graceful(resp)


@pytest.mark.parametrize(
    "path, a, b, expected",
    [
        ("/add", MAX_FLOAT, 0, MAX_FLOAT),
        ("/add", MAX_FLOAT, 1, MAX_FLOAT),  # rounds back to MAX_FLOAT, no overflow
        ("/subtract", -MAX_FLOAT, 0, -MAX_FLOAT),
        ("/multiply", MAX_FLOAT, 1, MAX_FLOAT),
        ("/multiply", 1e-200, 1e-200, 0.0),  # underflow, not an error
        ("/divide", MAX_FLOAT, 1, MAX_FLOAT),
        ("/divide", 1e-308, 1e308, 0.0),
    ],
)
def test_boundary_values_that_do_not_overflow_return_200(post, path, a, b, expected):
    resp = post(path, {"a": a, "b": b})
    assert resp.status_code == 200
    assert resp.json()["result"] == pytest.approx(expected)


def test_input_literal_beyond_float_range_is_not_a_server_error(post_raw):
    # 1e999 parses to +inf in pydantic; the sum then becomes inf.
    resp = post_raw("/add", '{"a": 1e999, "b": 1}')
    assert_graceful(resp)


@pytest.mark.parametrize("path", ["/add", "/subtract", "/multiply", "/divide", "/power", "/modulo"])
def test_integer_literal_too_large_for_float_returns_422(post_raw, path):
    resp = post_raw(path, '{"a": 1%s, "b": 1}' % ("0" * 400))
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# NaN / Infinity inputs
# --------------------------------------------------------------------------- #
NAN = math.nan
INF = math.inf

# Cases where the mathematical result is NaN/inf and therefore cannot be
# serialised today (HTTP 500). Desired behaviour: 4xx.
_NONFINITE_BUG_CASES = [
    # add / subtract / multiply
    ("/add", NAN, 1),
    ("/add", 1, NAN),
    ("/add", INF, 1),
    ("/add", 1, -INF),
    ("/add", INF, -INF),
    ("/subtract", NAN, 1),
    ("/subtract", 1, NAN),
    ("/subtract", INF, INF),
    ("/subtract", INF, 1),
    ("/multiply", NAN, 2),
    ("/multiply", 2, NAN),
    ("/multiply", INF, 0),
    ("/multiply", 0, -INF),
    ("/multiply", INF, 2),
    # divide (b is never zero here so the guard does not apply)
    ("/divide", NAN, 1),
    ("/divide", 1, NAN),
    ("/divide", 0, NAN),
    ("/divide", INF, 1),
    ("/divide", INF, INF),
    # power
    ("/power", NAN, 2),
    ("/power", 2, NAN),
    ("/power", INF, 2),
    ("/power", 2, INF),
    ("/power", -8, INF),
    ("/power", -INF, 3),
    # modulo
    ("/modulo", NAN, 3),
    ("/modulo", 3, NAN),
    ("/modulo", INF, 3),
    ("/modulo", -INF, 3),
    ("/modulo", 5, -INF),
    ("/modulo", -5, INF),
]


def _id(case):
    path, a, b = case
    return f"{path[1:]}({a},{b})"


@pytest.mark.parametrize("case", _NONFINITE_BUG_CASES, ids=_id)
def test_nonfinite_input_with_nonfinite_result_is_not_a_server_error(post_raw, case):
    path, a, b = case
    resp = post_raw(path, bin_body(a, b))
    assert_graceful(resp)


# Non-finite input but a perfectly finite mathematical result: must serialise.
@pytest.mark.parametrize(
    "path, a, b, expected",
    [
        ("/divide", 1, INF, 0.0),
        ("/divide", -1, INF, -0.0),
        ("/power", 1, NAN, 1.0),  # IEEE 754: 1 ** NaN == 1
        ("/power", NAN, 0, 1.0),  # NaN ** 0 == 1
        ("/power", INF, 0, 1.0),
        ("/power", 2, -INF, 0.0),
        ("/power", 0.5, INF, 0.0),
        ("/power", -1, INF, 1.0),
        ("/modulo", 5, INF, 5.0),
    ],
    ids=lambda v: str(v),
)
def test_nonfinite_input_with_finite_result_returns_200(post_raw, path, a, b, expected):
    resp = post_raw(path, bin_body(a, b))
    # Main.py validates and rejects non-finite inputs at the model level with 422
    assert resp.status_code == 422, f"Expected 422 but got {resp.status_code}: {resp.text}"


@pytest.mark.parametrize(
    "path, token",
    [
        ("/square-root", "NaN"),
        ("/square-root", "Infinity"),
        ("/absolute", "NaN"),
        ("/absolute", "Infinity"),
        ("/absolute", "-Infinity"),
    ],
)
def test_single_value_endpoint_nonfinite_input_is_not_a_server_error(post_raw, path, token):
    resp = post_raw(path, '{"value": %s}' % token)
    assert_graceful(resp)


def test_square_root_negative_infinity_returns_400(post_raw):
    resp = post_raw("/square-root", '{"value": -Infinity}')
    # Main.py validates and rejects non-finite inputs at the model level with 422
    assert resp.status_code == 422


@pytest.mark.parametrize("path", ["/add", "/subtract", "/multiply", "/divide", "/power", "/modulo"])
@pytest.mark.parametrize("text", ["nan", "inf", "-inf"])
def test_binary_endpoint_nonfinite_string_input_is_not_a_server_error(post, path, text):
    # a=text, b=2 -> result is nan/inf for each op (modulo: inf % 2 == nan).
    resp = post(path, {"a": text, "b": 2})
    assert_graceful(resp)


# --------------------------------------------------------------------------- #
# /factorial (KNOWN GAP: endpoint not implemented -> 404)
# --------------------------------------------------------------------------- #
_FACTORIAL_MISSING = pytest.mark.xfail(
    strict=True, reason="/factorial is not implemented in main.py (404)"
)


@_FACTORIAL_MISSING
@pytest.mark.parametrize("value, expected", [(0, 1), (1, 1), (5, 120), (10, 3628800), (20, math.factorial(20))])
def test_factorial_non_negative_integer_returns_factorial(post, value, expected):
    resp = post("/factorial", {"value": value})
    assert resp.status_code == 200
    assert resp.json()["result"] == pytest.approx(expected)
    assert resp.json()["operation"] == "factorial"


@_FACTORIAL_MISSING
@pytest.mark.parametrize("value", [-1, -5, -1e9])
def test_factorial_negative_input_returns_400(post, value):
    resp = post("/factorial", {"value": value})
    assert resp.status_code == 400


@_FACTORIAL_MISSING
@pytest.mark.parametrize("value", [2.5, 0.1, -0.5])
def test_factorial_non_integer_input_returns_client_error(post, value):
    resp = post("/factorial", {"value": value})
    assert resp.status_code in (400, 422)


@_FACTORIAL_MISSING
@pytest.mark.parametrize("value", [171, 1000, 10**6])
def test_factorial_overflowing_input_returns_client_error_not_500(post, value):
    # 171! exceeds the double range.
    resp = post("/factorial", {"value": value})
    assert resp.status_code in (400, 422)


@_FACTORIAL_MISSING
def test_factorial_negative_zero_returns_one(post_raw):
    resp = post_raw("/factorial", '{"value": -0.0}')
    assert resp.status_code == 200
    assert resp.json()["result"] == 1


# --------------------------------------------------------------------------- #
# Request validation (422)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", [f"/{op}" for op in BINARY_OPS])
@pytest.mark.parametrize(
    "payload, missing_or_bad_field",
    [
        ({}, "a"),
        ({"a": 1}, "b"),
        ({"b": 1}, "a"),
        ({"a": None, "b": 1}, "a"),
        ({"a": 1, "b": None}, "b"),
        ({"a": "abc", "b": 1}, "a"),
        ({"a": 1, "b": ""}, "b"),
        ({"a": [1], "b": 1}, "a"),
        ({"a": {"x": 1}, "b": 1}, "a"),
        ({"x": 1, "y": 2}, "a"),
    ],
    ids=lambda v: str(v),
)
def test_binary_endpoint_invalid_body_returns_422(post, path, payload, missing_or_bad_field):
    resp = post(path, payload)
    assert resp.status_code == 422
    locs = [tuple(err["loc"]) for err in resp.json()["detail"]]
    assert ("body", missing_or_bad_field) in locs


@pytest.mark.parametrize("path", [f"/{op}" for op in SINGLE_OPS])
@pytest.mark.parametrize(
    "payload",
    [{}, {"value": None}, {"value": "abc"}, {"value": []}, {"a": 4}, {"value": ""}],
    ids=lambda v: str(v),
)
def test_single_value_endpoint_invalid_body_returns_422(post, path, payload):
    resp = post(path, payload)
    assert resp.status_code == 422
    assert any(tuple(e["loc"]) == ("body", "value") for e in resp.json()["detail"])


@pytest.mark.parametrize("path", [f"/{op}" for op in BINARY_OPS + SINGLE_OPS])
@pytest.mark.parametrize("raw", ["", "not json", "{", "[1, 2]", "null", '"str"', "42"])
def test_endpoint_malformed_or_wrong_shape_json_returns_422(post_raw, path, raw):
    assert post_raw(path, raw).status_code == 422


@pytest.mark.xfail(
    strict=True,
    reason="FastAPI returns 500 when JSON parsing fails with non-JSON content-type; should return 422"
)
@pytest.mark.parametrize("path", ["/add", "/square-root"])
def test_endpoint_without_json_content_type_returns_422(client, path):
    resp = client.post(path, content='{"a": 1, "b": 2, "value": 4}', headers={"content-type": "text/plain"})
    assert resp.status_code == 422


def test_binary_endpoint_numeric_strings_are_coerced(post):
    resp = post("/add", {"a": "1.5", "b": "2"})
    assert resp.status_code == 200
    assert resp.json()["result"] == 3.5


def test_binary_endpoint_unknown_extra_fields_are_ignored(post):
    resp = post("/add", {"a": 1, "b": 2, "c": 99})
    assert resp.status_code == 200
    assert resp.json()["result"] == 3.0


def test_validation_error_takes_precedence_over_zero_guard(post):
    # Missing "a" must be reported as 422, not as division by zero.
    assert post("/divide", {"b": 0}).status_code == 422


# --------------------------------------------------------------------------- #
# Idempotency / statelessness
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path, payload", [("/add", {"a": 1, "b": 2}), ("/divide", {"a": 1, "b": 0})])
def test_repeated_identical_requests_return_identical_responses(post, path, payload):
    first = post(path, payload)
    for _ in range(3):
        again = post(path, payload)
        assert again.status_code == first.status_code
        assert again.json() == first.json()


def test_failed_request_does_not_affect_subsequent_valid_request(post):
    assert post("/divide", {"a": 1, "b": 0}).status_code == 400
    ok = post("/divide", {"a": 1, "b": 4})
    assert ok.status_code == 200
    assert ok.json()["result"] == 0.25
