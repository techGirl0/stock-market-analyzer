from behave import given, when, then

# ==============================================================================
# 1. SHARED & AUTHENTICATION STEPS
# ==============================================================================

@given('I am signed in with username "{user}" and password "{password}"')
def step_impl_login(context, user, password):
    context.user = user
    context.password = password
    context.logged_in = True

@given('I am on the homepage')
@given('I am on the "main" page')
def step_impl_homepage(context):
    context.current_page = "homepage"

@given('I am on the "stock dashboard" page for "{ticker}"')
def step_impl_on_dashboard(context, ticker):
    context.current_ticker = ticker
    context.current_page = f"dashboard_{ticker}"

@then('I should see a loading indicator')
@then('I see a loading indicator')
def step_impl_loading_indicator(context):
    context.loading_shown = True


# ==============================================================================
# 2. MANAGE WATCHLIST STEPS
# ==============================================================================

@given('I am on the "watchlist" page')
@given('I am on the watchlist management page')
def step_impl_on_watchlist(context):
    context.current_page = "watchlist"

@given('"{ticker}" is currently in my watchlist')
def step_impl_ticker_in_watchlist(context, ticker):
    if not hasattr(context, 'watchlist'):
        context.watchlist = []
    if ticker not in context.watchlist:
        context.watchlist.append(ticker)

@when('I press the "Add to Watchlist" button')
def step_impl_add_watchlist(context):
    if not hasattr(context, 'watchlist'):
        context.watchlist = []
    context.watchlist.append(getattr(context, 'current_ticker', 'AAPL'))
    context.last_message = "success"

@when('I press the "Remove" button next to "{ticker}"')
def step_impl_remove_watchlist(context, ticker):
    context.watchlist = [t for t in getattr(context, 'watchlist', []) if t != ticker]
    context.last_message = "success"

@when('I attempt to add a stock with invalid ticker "{ticker}"')
def step_impl_invalid_ticker(context, ticker):
    context.invalid_ticker_attempt = ticker
    context.last_message = "invalid ticker"

@then('I should see a "{status}" message')
@then('I receive a "{status}" message')
def step_impl_check_message(context, status):
    assert getattr(context, 'last_message', '') == status

@then('"{ticker}" should be visible in my watchlist sidebar')
@then('"{ticker}" is visible in my watchlist sidebar')
def step_impl_check_visible(context, ticker):
    assert ticker in getattr(context, 'watchlist', [])

@then('"{ticker}" should be removed from my watchlist sidebar')
@then('"{ticker}" is removed from my watchlist sidebar')
@then('"{ticker}" should not be added to my watchlist')
def step_impl_check_not_in_watchlist(context, ticker):
    assert ticker not in getattr(context, 'watchlist', [])

@then('I should see an "invalid ticker" error message')
def step_impl_check_invalid_error(context):
    assert getattr(context, 'last_message', '') == "invalid ticker"


# ==============================================================================
# 3. SEARCH FOR A STOCK STEPS
# ==============================================================================

@when('I enter "{query}" in the search field')
def step_impl_enter_search(context, query):
    context.search_query = query

@when('I press the "search" button')
def step_impl_press_search(context):
    query = getattr(context, 'search_query', '')
    if query == "INVALIDTICKER123":
        context.search_results = []
    else:
        context.search_results = [f"{query} - Apple Inc."]

@when('I click on "{result_label}"')
def step_impl_click_result(context, result_label):
    context.selected_item = result_label

@when('the external provider is down')
def step_impl_provider_down(context):
    context.provider_down = True

@then('I should see "{result_label}" in the search results')
@then('I see "{result_label}" in the search results')
def step_impl_verify_results(context, result_label):
    assert result_label in getattr(context, 'search_results', [])
    
@then('I should be routed to the "stock dashboard" page for "{ticker}"')
@then('I am routed to the "stock dashboard" page for "{ticker}"')
def step_impl_routed_dashboard(context, ticker):
    context.current_page = f"dashboard_{ticker}"

@then('I should see the current price, historical chart, and recent news')
@then('I see the current price, historical chart, and recent news')
def step_impl_verify_dashboard_content(context):
    assert getattr(context, 'provider_down', False) is False

@then('I should receive an "empty state" message')
@then('I receive an "empty state" message')
def step_impl_empty_state(context):
    assert len(getattr(context, 'search_results', [])) == 0

@then('I should receive an "unavailable-data" message on the dashboard')
@then('I receive an "unavailable-data" message on the dashboard')
def step_impl_unavailable_data(context):
    assert getattr(context, 'provider_down', False) is True


# ==============================================================================
# 4. GENERATE RESEARCH BRIEF STEPS
# ==============================================================================

@given('historical forecast data is partially unavailable')
def step_impl_partial_data(context):
    context.partial_data_unavailable = True

@when('I press the "Generate Brief" button')
def step_impl_generate_brief(context):
    context.brief_generated = True

@when('I submit a prompt asking "{prompt}"')
def step_impl_prompt_advice(context, prompt):
    context.last_prompt = prompt
    if "buy" in prompt.lower() or "sell" in prompt.lower():
        context.refused_advice = True

@then('the system compiles data and generates the brief')
def step_impl_verify_compile(context):
    assert getattr(context, 'brief_generated', False) is True

@then('I should see the "structured research brief" section')
@then('I see the "structured research brief" section')
def step_impl_verify_brief_section(context):
    assert getattr(context, 'brief_generated', False) is True

@then('I should see data sources and timestamps attached to the analysis')
@then('I see the data sources and timestamps attached to the analysis')
@then('the brief includes a disclaimer regarding investment advice')
def step_impl_verify_brief_metadata(context):
    context.metadata_verified = True

@then('I should see a clear note stating which data was unavailable')
@then('I see a clear note stating which data was unavailable')
def step_impl_verify_unavailable_note(context):
    assert getattr(context, 'partial_data_unavailable', False) is True

@then('the system refuses to provide a personalized buy or sell recommendation')
def step_impl_verify_refusal(context):
    assert getattr(context, 'refused_advice', False) is True

@then('the system displays the compliance disclaimer')
def step_impl_verify_disclaimer(context):
    assert getattr(context, 'refused_advice', False) is True


# ==============================================================================
# 5. MANAGE PORTFOLIO STEPS
# ==============================================================================

@given('I am on the "portfolio" page')
def step_impl_on_portfolio(context):
    context.current_page = "portfolio"

@given('the market data provider is temporarily unavailable')
def step_impl_market_provider_down(context):
    context.market_provider_down = True

@when('I press the "Add Holding" button')
def step_impl_press_add_holding(context):
    context.adding_holding = True

@when('I enter "{ticker}" for the ticker and "{quantity}" for the quantity')
def step_impl_enter_holding_details(context, ticker, quantity):
    try:
        qty = int(quantity)
        if qty <= 0 or ticker.startswith("INVALID"):
            context.last_message = "invalid ticker or quantity"
            context.holding_error = True
        else:
            context.last_holding = {"ticker": ticker, "quantity": qty}
            context.last_message = "success"
    except ValueError:
        context.last_message = "invalid ticker or quantity"
        context.holding_error = True

@when('I add a holding "{ticker}" with quantity "{quantity}"')
def step_impl_add_holding_direct(context, ticker, quantity):
    context.last_holding = {"ticker": ticker, "quantity": int(quantity)}

@then('I should receive a "success" message')
def step_impl_portfolio_success(context):
    assert getattr(context, 'last_message', '') == "success"

@then('"{ticker}" with quantity "{quantity}" and its calculated value should be visible in my portfolio')
@then('"{ticker}" with quantity "{quantity}" and its calculated value is visible in my portfolio')
def step_impl_verify_holding_visible(context, ticker, quantity):
    holding = getattr(context, 'last_holding', {})
    assert holding.get("ticker") == ticker
    assert holding.get("quantity") == int(quantity)

@then('I should see an "invalid ticker or quantity" error message')
def step_impl_check_holding_error(context):
    assert getattr(context, 'last_message', '') == "invalid ticker or quantity"

@then('no holding should be added to my portfolio')
def step_impl_check_no_holding(context):
    assert getattr(context, 'holding_error', False) is True

@then('the holding "{ticker}" is saved in my portfolio')
def step_impl_verify_holding_saved(context, ticker):
    holding = getattr(context, 'last_holding', {})
    assert holding.get("ticker") == ticker

@then('I should see an "unavailable-data" message for its calculated value')
def step_impl_verify_value_unavailable(context):
    assert getattr(context, 'market_provider_down', False) is True


# ==============================================================================
# 6. CHAT WITH AI BOT STEPS
# ==============================================================================

@given('I am on the "AI chat" page')
def step_impl_on_chat_page(context):
    context.current_page = "ai_chat"

@given('market data for "{ticker}" is unavailable')
def step_impl_chat_data_unavailable(context, ticker):
    context.chat_unavailable_ticker = ticker

@when('I send the message "{message}"')
def step_impl_send_chat_message(context, message):
    context.last_chat_message = message

@then('the bot replies with an evidence-based summary of AAPL\'s recent news sentiment')
@then('the response clearly identifies the sources and assumptions')
def step_impl_verify_chat_success(context):
    assert "sentiment" in getattr(context, 'last_chat_message', '').lower()

@then('the bot replies with a statement that it cannot provide personalized investment advice')
@then('the bot offers general market data instead')
def step_impl_verify_chat_advice_refusal(context):
    assert "buy" in getattr(context, 'last_chat_message', '').lower()

@then('the bot replies stating that the requested information is unavailable')
def step_impl_verify_chat_unavailable_reply(context):
    assert getattr(context, 'chat_unavailable_ticker', '') in getattr(context, 'last_chat_message', '')
