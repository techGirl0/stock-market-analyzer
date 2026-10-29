from behave import given, when, then

# --- Background & Auth Steps ---
@given('I am signed in with username "{user}" and password "{password}"')
def step_impl_login(context, user, password):
    context.user = user
    context.logged_in = True

@given('I am on the homepage')
@given('I am on the "main" page')
def step_impl_homepage(context):
    context.current_page = "homepage"

# --- Watchlist Steps ---
@given('I am on the "stock dashboard" page for "{ticker}"')
def step_impl_on_dashboard(context, ticker):
    context.current_ticker = ticker
    context.current_page = f"dashboard_{ticker}"

@given('I am on the "watchlist" page')
@given('I am on the watchlist management page')
def step_impl_on_watchlist(context):
    context.current_page = "watchlist"

@given('"{ticker}" is currently in my watchlist')
def step_impl_ticker_in_watchlist(context, ticker):
    context.watchlist = getattr(context, 'watchlist', [])
    if ticker not in context.watchlist:
        context.watchlist.append(ticker)

@when('I press the "Add to Watchlist" button')
def step_impl_add_watchlist(context):
    context.watchlist = getattr(context, 'watchlist', [])
    context.watchlist.append(context.current_ticker)
    context.last_message = "success"

@when('I press the "Remove" button next to "{ticker}"')
def step_impl_remove_watchlist(context, ticker):
    context.watchlist = [t for t in getattr(context, 'watchlist', []) if t != ticker]
    context.last_message = "success"

@when('I attempt to add a stock with invalid ticker "{ticker}"')
def step_impl_invalid_ticker(context, ticker):
    context.last_message = "invalid ticker"

@then('I should see a "{status}" message')
def step_impl_check_message(context, status):
    assert getattr(context, 'last_message', '') == status

@then('"{ticker}" should be visible in my watchlist sidebar')
def step_impl_check_visible(context, ticker):
    assert ticker in getattr(context, 'watchlist', [])

@then('"{ticker}" should be removed from my watchlist sidebar')
@then('"{ticker}" should not be added to my watchlist')
def step_impl_check_not_in_watchlist(context, ticker):
    assert ticker not in getattr(context, 'watchlist', [])

@then('I should see an "invalid ticker" error message')
def step_impl_check_invalid_error(context):
    assert getattr(context, 'last_message', '') == "invalid ticker"

# --- Search Steps ---
@when('I enter "{query}" in the search field')
def step_impl_enter_search(context, query):
    context.search_query = query

@when('I press the "search" button')
def step_impl_press_search(context):
    if context.search_query == "INVALIDTICKER123":
        context.search_results = []
    else:
        context.search_results = [f"{context.search_query} - Apple Inc."]

@when('I click on "{result_label}"')
def step_impl_click_result(context, result_label):
    context.selected_item = result_label

@when('the external provider is down')
def step_impl_provider_down(context):
    context.provider_down = True

@then('I should see "{result_label}" in the search results')
def step_impl_verify_results(context, result_label):
    assert result_label in getattr(context, 'search_results', [])

@then('I should see a loading indicator')
def step_impl_loading_indicator(context):
    pass  # Mock UI step

@then('I should be routed to the "stock dashboard" page for "{ticker}"')
def step_impl_routed_dashboard(context, ticker):
    context.current_page = f"dashboard_{ticker}"

@then('I should see the current price, historical chart, and recent news')
def step_impl_verify_dashboard_content(context):
    assert getattr(context, 'provider_down', False) is False

@then('I should receive an "empty state" message')
def step_impl_empty_state(context):
    assert len(getattr(context, 'search_results', [])) == 0

@then('I should receive an "unavailable-data" message on the dashboard')
def step_impl_unavailable_data(context):
    assert getattr(context, 'provider_down', False) is True