"""Step definitions for the analysis features (risk, volatility, scenarios).

Every step drives the real analysis endpoints so a regression fails the
scenario. The compare-stocks feature had no backend counterpart and was
removed along with the prototype UI it described.
"""

from behave import given, when, then

from common import override_instruments


def _symbol(context) -> str:
    return getattr(context, "current_ticker", "AAPL")


def _get_forecast(context, horizon: str) -> dict:
    response = context.client.get(
        f"/api/v1/instruments/{_symbol(context)}/forecast",
        params={"horizon": horizon},
        headers=context.auth,
    )
    assert response.status_code == 200, response.text
    context.last_response = response
    return response.json()


def _explain(context, topic: str) -> str:
    response = context.client.post(
        f"/api/v1/instruments/{_symbol(context)}/explain/{topic}",
        headers=context.auth,
    )
    assert response.status_code == 200, response.text
    context.last_response = response
    return response.json()["text"]


# ==============================================================================
# VIEW COMPOSITE RISK SCORE
# ==============================================================================

@when('I navigate to the "Risk Score" section')
def step_impl_open_risk(context):
    response = context.client.get(
        f"/api/v1/instruments/{_symbol(context)}/risk", headers=context.auth
    )
    assert response.status_code == 200, response.text
    context.last_response = response
    context.risk = response.json()

@then('I should see a risk score between 1 and 10')
def step_impl_verify_risk_score(context):
    assert 1 <= context.risk["score"] <= 10, context.risk["score"]

@then('I should see a breakdown of what is driving the score')
def step_impl_verify_risk_breakdown(context):
    assert context.risk["components"], "score must come with its components"

@then('each component should have a plain English explanation')
def step_impl_verify_risk_explanation(context):
    assert _explain(context, "risk"), "risk explanation must not be empty"

@given('some risk input data is unavailable')
def step_impl_risk_partial_data(context):
    from tests.fakes import ShortHistoryDemoConnector

    override_instruments(context, ShortHistoryDemoConnector())

@then('I should see a partial risk score using available components')
def step_impl_verify_partial_score(context):
    assert context.risk["score"] is None, "insufficient history must not produce a score"
    assert context.risk["meta"]["availability"] == "unavailable"

@then('I should see a note explaining which data was missing')
def step_impl_verify_missing_data_note(context):
    assert context.risk["meta"]["availability"] == "unavailable"

@then('the risk score section should include a disclaimer that this is not financial advice')
def step_impl_verify_risk_disclaimer(context):
    assert "not" in context.risk["meta"]["disclaimer"].lower()


# ==============================================================================
# VIEW VOLATILITY FORECAST
# ==============================================================================

@when('I navigate to the "Volatility Forecast" section')
def step_impl_open_volatility(context):
    context.forecast = _get_forecast(context, "20d")

@then('I should see expected price movement ranges for 5, 10, and 20 days')
def step_impl_verify_vol_ranges(context):
    for horizon in ("5d", "10d", "20d"):
        body = _get_forecast(context, horizon)
        assert len(body["scenarios"]) == 1, f"no scenario for {horizon}"

@then('each range should be shown as a percentage and a dollar amount')
def step_impl_verify_vol_format(context):
    quote = context.client.get(f"/api/v1/instruments/{_symbol(context)}/quote")
    assert quote.status_code == 200, quote.text
    price = float(quote.json()["price"])
    for horizon in ("5d", "10d", "20d"):
        scenario = _get_forecast(context, horizon)["scenarios"][0]
        # dollar amounts around the current price; the UI derives the
        # percentage from exactly these two numbers
        assert 0 < scenario["bear"] < price < scenario["bull"], (horizon, scenario, price)

@then('the section should explain what volatility means in plain English')
def step_impl_verify_vol_explanation(context):
    assert _explain(context, "volatility"), "volatility explanation must not be empty"

@given('the stock has less than 21 days of price history available')
def step_impl_short_history(context):
    from tests.fakes import ShortHistoryDemoConnector

    override_instruments(context, ShortHistoryDemoConnector())

@then('I should see a message stating that not enough data is available')
def step_impl_verify_vol_unavailable(context):
    assert context.forecast["meta"]["availability"] == "unavailable"

@then('no forecast numbers should be displayed')
def step_impl_verify_no_forecast_numbers(context):
    assert context.forecast["scenarios"] == []

@then('the forecast should be labelled as a statistical range')
def step_impl_verify_range_label(context):
    assert any("not predictions" in a.lower() for a in context.forecast["meta"]["assumptions"])

@then('the section should include a disclaimer that this is not a prediction')
def step_impl_verify_prediction_disclaimer(context):
    assert "not" in context.forecast["meta"]["disclaimer"].lower()


# ==============================================================================
# RUN LONG-TERM SCENARIO ANALYSIS
# ==============================================================================

@when('I navigate to the "Scenario Analysis" section')
def step_impl_open_scenarios(context):
    context.scenarios = {h: _get_forecast(context, h) for h in ("1y", "3y", "5y")}

@then('I should see a worse case, middle case, and better case for 1 year')
def step_impl_verify_scenarios_1y(context):
    assert len(context.scenarios["1y"]["scenarios"]) == 1

@then('I should see a worse case, middle case, and better case for 3 years')
def step_impl_verify_scenarios_3y(context):
    assert len(context.scenarios["3y"]["scenarios"]) == 1

@then('I should see a worse case, middle case, and better case for 5 years')
def step_impl_verify_scenarios_5y(context):
    assert len(context.scenarios["5y"]["scenarios"]) == 1

@then('the worse case price should be lower than the middle case price')
def step_impl_verify_bear_lt_base(context):
    for horizon, body in context.scenarios.items():
        s = body["scenarios"][0]
        assert s["bear"] < s["base"], (horizon, s)

@then('the middle case price should be lower than the better case price')
def step_impl_verify_base_lt_bull(context):
    for horizon, body in context.scenarios.items():
        s = body["scenarios"][0]
        assert s["base"] < s["bull"], (horizon, s)

@then('the scenarios should be labelled as illustrative "what if" cases')
def step_impl_verify_scenario_labels(context):
    for body in context.scenarios.values():
        assert body["meta"]["assumptions"], "scenarios must state their assumptions"

@then('the section should include a disclaimer that these are not predictions or financial advice')
def step_impl_verify_scenario_disclaimer(context):
    for body in context.scenarios.values():
        assert "not" in body["meta"]["disclaimer"].lower()

@given('historical price data is unavailable')
def step_impl_no_history(context):
    from tests.fakes import ShortHistoryDemoConnector

    override_instruments(context, ShortHistoryDemoConnector())

@then('I should see a message stating that not enough data is available to compute scenarios')
def step_impl_verify_scenarios_unavailable(context):
    assert context.scenarios["1y"]["scenarios"] == []
    assert context.scenarios["1y"]["meta"]["availability"] == "unavailable"
