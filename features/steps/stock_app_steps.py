"""Step definitions that exercise the real API via the TestClient.

The watchlist, search, brief, portfolio and chat scenarios all drive the
actual backend so a regression fails the scenario.
"""

from behave import given, when, then

from common import override_instruments


# ==============================================================================
# 1. SHARED & AUTHENTICATION STEPS
# ==============================================================================

@given('I am signed in with username "{user}" and password "{password}"')
def step_impl_login(context, user, password):
    context.user = user
    context.password = password
    # A fresh account per scenario: scenarios must not see each other's data.
    from uuid import uuid4

    email = f"{user.lower()}-{uuid4().hex[:8]}@example.com"
    response = context.client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    if response.status_code not in (201, 409):
        raise AssertionError(response.text)
    response = context.client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    context.auth = {"Authorization": f"Bearer {response.json()['access_token']}"}
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
    # The UI spinner is frontend behaviour; against the backend the
    # equivalent is: the request was made and completed.
    assert getattr(context, "last_response", None) is not None, "no request was made"


# ==============================================================================
# 2. MANAGE WATCHLIST STEPS
# ==============================================================================

@given('I am on the "watchlist" page')
@given('I am on the watchlist management page')
def step_impl_on_watchlist(context):
    context.current_page = "watchlist"

@given('"{ticker}" is currently in my watchlist')
def step_impl_ticker_in_watchlist(context, ticker):
    response = context.client.get("/api/v1/watchlists", headers=context.auth)
    assert response.status_code == 200, response.text
    lists = response.json()
    if not lists:
        created = context.client.post(
            "/api/v1/watchlists", headers=context.auth, json={"name": "Scenario"}
        )
        assert created.status_code == 201, created.text
        lists = [created.json()]
    context.watchlist_id = lists[0]["id"]
    added = context.client.post(
        f"/api/v1/watchlists/{context.watchlist_id}/items",
        headers=context.auth,
        json={"symbol": ticker},
    )
    assert added.status_code in (201, 409), added.text

@when('I press the "Add to Watchlist" button')
def step_impl_add_watchlist(context):
    lists = context.client.get("/api/v1/watchlists", headers=context.auth).json()
    if not lists:
        created = context.client.post(
            "/api/v1/watchlists", headers=context.auth, json={"name": "Scenario"}
        )
        assert created.status_code == 201, created.text
        lists = [created.json()]
    context.watchlist_id = lists[0]["id"]
    response = context.client.post(
        f"/api/v1/watchlists/{context.watchlist_id}/items",
        headers=context.auth,
        json={"symbol": getattr(context, "current_ticker", "AAPL")},
    )
    assert response.status_code == 201, response.text
    context.last_message = "success"

@when('I press the "Remove" button next to "{ticker}"')
def step_impl_remove_watchlist(context, ticker):
    lists = context.client.get("/api/v1/watchlists", headers=context.auth).json()
    items = lists[0]["items"]
    item = next(item for item in items if item["symbol"] == ticker)
    response = context.client.delete(
        f"/api/v1/watchlists/{lists[0]['id']}/items/{item['id']}",
        headers=context.auth,
    )
    assert response.status_code == 204, response.text
    context.last_message = "success"

@when('I attempt to add a stock with invalid ticker "{ticker}"')
def step_impl_invalid_ticker(context, ticker):
    context.invalid_ticker_attempt = ticker
    lists = context.client.get("/api/v1/watchlists", headers=context.auth).json()
    if not lists:
        created = context.client.post(
            "/api/v1/watchlists", headers=context.auth, json={"name": "Scenario"}
        )
        assert created.status_code == 201, created.text
        lists = [created.json()]
    response = context.client.post(
        f"/api/v1/watchlists/{lists[0]['id']}/items",
        headers=context.auth,
        json={"symbol": ticker},
    )
    assert response.status_code == 404, response.text
    context.last_message = "invalid ticker"

@then('I should see a "{status}" message')
@then('I receive a "{status}" message')
def step_impl_check_message(context, status):
    assert getattr(context, 'last_message', '') == status

@then('"{ticker}" should be visible in my watchlist sidebar')
@then('"{ticker}" is visible in my watchlist sidebar')
def step_impl_check_visible(context, ticker):
    lists = context.client.get("/api/v1/watchlists", headers=context.auth).json()
    assert ticker in [item["symbol"] for item in lists[0]["items"]]

@then('"{ticker}" should be removed from my watchlist sidebar')
@then('"{ticker}" is removed from my watchlist sidebar')
@then('"{ticker}" should not be added to my watchlist')
def step_impl_check_not_in_watchlist(context, ticker):
    lists = context.client.get("/api/v1/watchlists", headers=context.auth).json()
    assert ticker not in [item["symbol"] for item in lists[0]["items"]]

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
    response = context.client.get(
        "/api/v1/instruments/search", params={"q": context.search_query}
    )
    assert response.status_code == 200, response.text
    context.search_results = response.json()["items"]
    context.last_response = response

@when('I click on "{result_label}"')
def step_impl_click_result(context, result_label):
    # The dashboard for a symbol is backed by its quote.
    symbol = result_label.split(" - ")[0]
    response = context.client.get(f"/api/v1/instruments/{symbol}/quote")
    context.last_response = response
    if response.status_code == 200:
        context.dashboard_symbol = symbol
    else:
        context.dashboard_symbol = None
        context.dashboard_error = response.json()["error"]["code"]

@when('the external provider is down')
def step_impl_provider_down(context):
    from tests.fakes import ProviderDownConnector

    override_instruments(context, ProviderDownConnector())

@then('I should see "{result_label}" in the search results')
@then('I see "{result_label}" in the search results')
def step_impl_verify_results(context, result_label):
    symbol, _, name = result_label.partition(" - ")
    matches = [
        item for item in getattr(context, "search_results", [])
        if item["symbol"] == symbol and name in item["name"]
    ]
    assert matches, f"{result_label} not found in search results"

@then('I should be routed to the "stock dashboard" page for "{ticker}"')
@then('I am routed to the "stock dashboard" page for "{ticker}"')
def step_impl_routed_dashboard(context, ticker):
    assert getattr(context, "dashboard_symbol", None) == ticker

@then('I should see the current price, historical chart, and recent news')
@then('I see the current price, historical chart, and recent news')
def step_impl_verify_dashboard_content(context):
    symbol = context.dashboard_symbol
    quote = context.client.get(f"/api/v1/instruments/{symbol}/quote")
    history = context.client.get(f"/api/v1/instruments/{symbol}/history")
    news = context.client.get(f"/api/v1/instruments/{symbol}/news")
    assert quote.status_code == 200 and quote.json()["price"] is not None
    assert history.status_code == 200 and history.json()["items"]
    assert news.status_code == 200

@then('I should receive an "empty state" message')
@then('I receive an "empty state" message')
def step_impl_empty_state(context):
    assert getattr(context, 'search_results', []) == []

@then('I should receive an "unavailable-data" message on the dashboard')
@then('I receive an "unavailable-data" message on the dashboard')
def step_impl_unavailable_data(context):
    response = context.client.get(f"/api/v1/instruments/{context.dashboard_symbol}/quote")
    assert response.status_code == 503, response.text
    assert response.json()["error"]["code"] == "provider_unavailable"


# ==============================================================================
# 4. GENERATE RESEARCH BRIEF STEPS
# ==============================================================================

@given('historical forecast data is partially unavailable')
def step_impl_partial_data(context):
    from tests.fakes import NoNewsDemoConnector

    override_instruments(context, NoNewsDemoConnector())

@when('I press the "Generate Brief" button')
def step_impl_generate_brief(context):
    symbol = getattr(context, "current_ticker", "NVDA")
    response = context.client.post(f"/api/v1/instruments/{symbol}/brief", headers=context.auth)
    context.last_response = response
    if response.status_code == 200:
        context.brief = response.json()
    else:
        context.brief = None
        context.brief_error = response.json()["error"]["code"]

@when('I submit a prompt asking "{prompt}"')
def step_impl_prompt_advice(context, prompt):
    symbol = getattr(context, "current_ticker", "NVDA")
    response = context.client.post(
        f"/api/v1/instruments/{symbol}/chat",
        headers=context.auth,
        json={"messages": [], "user_message": prompt},
    )
    context.last_response = response
    assert response.status_code == 200, response.text
    context.chat_reply = response.json()["reply"]

@then('the system compiles data and generates the brief')
@then('I should see the "structured research brief" section')
@then('I see the "structured research brief" section')
def step_impl_verify_brief_section(context):
    assert getattr(context, "brief", None) is not None, getattr(context, "brief_error", "no brief")
    assert context.brief["brief_text"], "brief text must not be empty"

@then('I should see data sources and timestamps attached to the analysis')
@then('I see the data sources and timestamps attached to the analysis')
def step_impl_verify_brief_metadata(context):
    assert context.brief["sources"], "brief must cite its sources"
    assert context.brief["as_of"], "brief must state the data timestamp"

@then('the brief includes a disclaimer regarding investment advice')
def step_impl_verify_brief_disclaimer(context):
    assert "not" in context.brief["disclaimer"].lower()

@then('I should see a clear note stating which data was unavailable')
@then('I see a clear note stating which data was unavailable')
def step_impl_verify_unavailable_note(context):
    assert context.brief["limitations"], "partial data must produce limitations"
    assert any("unavailable" in lim.lower() for lim in context.brief["limitations"])

@then('the system refuses to provide a personalized buy or sell recommendation')
def step_impl_verify_refusal(context):
    reply = context.chat_reply
    assert "buy, sell or hold advice" in reply.lower(), reply

@then('the system displays the compliance disclaimer')
def step_impl_verify_disclaimer(context):
    assert "the decision is yours" in context.chat_reply.lower()


# ==============================================================================
# 5. MANAGE PORTFOLIO STEPS
# ==============================================================================

@given('I am on the "portfolio" page')
def step_impl_on_portfolio(context):
    context.current_page = "portfolio"

@given('the market data provider becomes temporarily unavailable')
def step_impl_market_provider_down(context):
    from tests.fakes import ProviderDownConnector

    override_instruments(context, ProviderDownConnector())

@when('I press the "Add Holding" button')
def step_impl_press_add_holding(context):
    context.adding_holding = True

def _ensure_portfolio(context):
    portfolios = context.client.get("/api/v1/portfolios", headers=context.auth).json()
    if portfolios:
        return portfolios[0]["id"]
    created = context.client.post("/api/v1/portfolios", headers=context.auth, json={"name": "Scenario"})
    assert created.status_code == 201, created.text
    return created.json()["id"]

def _add_holding(context, ticker, quantity):
    portfolio_id = _ensure_portfolio(context)
    context.portfolio_id = portfolio_id
    response = context.client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        headers=context.auth,
        json={"symbol": ticker, "quantity": float(quantity)},
    )
    if response.status_code == 201:
        context.last_message = "success"
        context.last_holding = response.json()
    else:
        context.last_message = "invalid ticker or quantity"
        context.holding_error = response.json()["error"]["code"]

@when('I enter "{ticker}" for the ticker and "{quantity}" for the quantity')
def step_impl_enter_holding_details(context, ticker, quantity):
    _add_holding(context, ticker, quantity)

@when('I add a holding "{ticker}" with quantity "{quantity}"')
@given('I add a holding "{ticker}" with quantity "{quantity}"')
def step_impl_add_holding_direct(context, ticker, quantity):
    _add_holding(context, ticker, quantity)

@then('I should receive a "success" message')
def step_impl_portfolio_success(context):
    assert getattr(context, 'last_message', '') == "success"

def _portfolio_holdings(context):
    assert getattr(context, "portfolio_id", None), "no portfolio was created"
    body = context.client.get(f"/api/v1/portfolios/{context.portfolio_id}", headers=context.auth).json()
    return body["holdings"]

@then('"{ticker}" with quantity "{quantity}" and its calculated value should be visible in my portfolio')
@then('"{ticker}" with quantity "{quantity}" and its calculated value is visible in my portfolio')
def step_impl_verify_holding_visible(context, ticker, quantity):
    holdings = _portfolio_holdings(context)
    holding = next(h for h in holdings if h["symbol"] == ticker)
    assert holding["quantity"] == float(quantity)
    assert holding["current_value"] is not None, "calculated value must be present"

@then('I should see an "invalid ticker or quantity" error message')
def step_impl_check_holding_error(context):
    assert getattr(context, 'last_message', '') == "invalid ticker or quantity"

@then('no holding should be added to my portfolio')
def step_impl_check_no_holding(context):
    assert _portfolio_holdings(context) == []

@then('the holding "{ticker}" is saved in my portfolio')
def step_impl_verify_holding_saved(context, ticker):
    assert any(h["symbol"] == ticker for h in _portfolio_holdings(context))

@then('I should see an "unavailable-data" message for its calculated value')
def step_impl_verify_value_unavailable(context):
    holdings = _portfolio_holdings(context)
    assert holdings
    assert all(h["current_value"] is None for h in holdings), "values must be unavailable, not defaulted"


# ==============================================================================
# 6. CHAT WITH AI BOT STEPS
# ==============================================================================

@given('I am on the "AI chat" page')
def step_impl_on_chat_page(context):
    context.current_page = "ai_chat"
    context.chat_symbol = "AAPL"

@given('market data for "{ticker}" is unavailable')
def step_impl_chat_data_unavailable(context, ticker):
    context.chat_symbol = ticker

@when('I send the message "{message}"')
def step_impl_send_chat_message(context, message):
    response = context.client.post(
        f"/api/v1/instruments/{context.chat_symbol}/chat",
        headers=context.auth,
        json={"messages": [], "user_message": message},
    )
    context.last_response = response
    if response.status_code == 200:
        context.chat_reply = response.json()["reply"]
        context.chat_error = None
    else:
        context.chat_reply = None
        context.chat_error = response.json()["error"]["code"]

@then('the bot replies with an evidence-based summary of AAPL\'s recent news sentiment')
def step_impl_verify_chat_success(context):
    assert context.chat_error is None, context.chat_error
    assert context.chat_reply, "reply must not be empty"

@then('the response clearly identifies the sources and assumptions')
def step_impl_verify_chat_metadata(context):
    assert context.last_response.json()["disclaimer"]
    assert context.last_response.json()["generated_at"]

@then('the bot replies with a statement that it cannot provide personalized investment advice')
def step_impl_verify_chat_advice_refusal(context):
    assert "buy, sell or hold advice" in context.chat_reply.lower()

@then('the bot offers general market data instead')
def step_impl_verify_chat_alternatives(context):
    assert "risk score" in context.chat_reply.lower()

@then('the bot replies stating that the requested information is unavailable')
def step_impl_verify_chat_unavailable_reply(context):
    # Unknown symbols are rejected up front: the API's "information
    # unavailable" answer for chat is the ticker_not_found error.
    assert context.chat_error == "ticker_not_found", context.chat_error
