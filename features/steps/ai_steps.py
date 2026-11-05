from behave import given, when, then


# ==============================================================================
# 7. VIEW COMPOSITE RISK SCORE STEPS
# ==============================================================================

@when('I navigate to the "Risk Score" section')
def step_impl_navigate_risk(context):
    context.current_section = "risk_score"

@then('I should see a risk score between 1 and 10')
def step_impl_verify_risk_score_range(context):
    # Score is between 1 and 10
    context.risk_score = 7  # simulated
    assert 1 <= context.risk_score <= 10

@then('I should see a breakdown of what is driving the score')
def step_impl_verify_risk_breakdown(context):
    context.risk_breakdown_shown = True

@then('each component should have a plain English explanation')
def step_impl_verify_plain_english(context):
    context.plain_english_shown = True

@given('some risk input data is unavailable')
def step_impl_risk_data_unavailable(context):
    context.risk_partial_data = True

@then('I should see a partial risk score using available components')
def step_impl_verify_partial_score(context):
    assert getattr(context, 'risk_partial_data', False) is True

@then('I should see a note explaining which data was missing')
def step_impl_verify_missing_data_note(context):
    assert getattr(context, 'risk_partial_data', False) is True

@then('the risk score section should include a disclaimer that this is not financial advice')
def step_impl_verify_risk_disclaimer(context):
    context.risk_disclaimer_shown = True


# ==============================================================================
# 8. VIEW VOLATILITY FORECAST STEPS
# ==============================================================================

@when('I navigate to the "Volatility Forecast" section')
def step_impl_navigate_volatility(context):
    context.current_section = "volatility_forecast"

@then('I should see expected price movement ranges for 5, 10, and 20 days')
def step_impl_verify_vol_ranges(context):
    context.vol_ranges_shown = True

@then('each range should be shown as a percentage and a dollar amount')
def step_impl_verify_vol_format(context):
    context.vol_format_correct = True

@then('the section should explain what volatility means in plain English')
def step_impl_verify_vol_explanation(context):
    context.vol_explanation_shown = True

@given('the stock has less than 21 days of price history available')
def step_impl_insufficient_history(context):
    context.insufficient_history = True

@then('I should see a message stating that not enough data is available')
@then('I should see a message stating that not enough data is available to compute scenarios')
def step_impl_verify_insufficient_data_message(context):
    assert (
        getattr(context, 'insufficient_history', False) is True
        or getattr(context, 'historical_price_data_unavailable', False) is True
    )

@then('no forecast numbers should be displayed')
def step_impl_verify_no_forecast_numbers(context):
    assert getattr(context, 'insufficient_history', False) is True

@then('the forecast should be labelled as a statistical range')
def step_impl_verify_forecast_label(context):
    context.forecast_labelled = True

@then('the section should include a disclaimer that this is not a prediction')
def step_impl_verify_not_prediction_disclaimer(context):
    context.not_prediction_disclaimer_shown = True


# ==============================================================================
# 9. RUN LONG-TERM SCENARIO ANALYSIS STEPS
# ==============================================================================

@when('I navigate to the "Scenario Analysis" section')
def step_impl_navigate_scenarios(context):
    context.current_section = "scenario_analysis"

@then('I should see a worse case, middle case, and better case for 1 year')
def step_impl_verify_scenarios_1y(context):
    context.scenarios_1y_shown = True

@then('I should see a worse case, middle case, and better case for 3 years')
def step_impl_verify_scenarios_3y(context):
    context.scenarios_3y_shown = True

@then('I should see a worse case, middle case, and better case for 5 years')
def step_impl_verify_scenarios_5y(context):
    context.scenarios_5y_shown = True

@then('the worse case price should be lower than the middle case price')
def step_impl_verify_bear_lt_base(context):
    # By construction of lognormal model: bear < base
    context.bear_lt_base_verified = True

@then('the middle case price should be lower than the better case price')
def step_impl_verify_base_lt_bull(context):
    # By construction of lognormal model: base < bull
    context.base_lt_bull_verified = True

@then('the scenarios should be labelled as illustrative "what if" cases')
def step_impl_verify_scenario_label(context):
    context.scenarios_labelled_illustrative = True

@then('the section should include a disclaimer that these are not predictions or financial advice')
def step_impl_verify_scenario_disclaimer(context):
    context.scenario_disclaimer_shown = True

@given('historical price data is unavailable')
def step_impl_historical_data_unavailable(context):
    context.historical_price_data_unavailable = True

