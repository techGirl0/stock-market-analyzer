Feature: Manage Watchlist
  As an authenticated user
  I want to add and remove stocks from my watchlist
  In order to track my preferred stocks and receive news alerts.

  Background:
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the homepage

  Scenario: Add stock to watchlist successfully (Happy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I press the "Add to Watchlist" button
    Then I should see a "success" message
    And "AAPL" should be visible in my watchlist sidebar

  Scenario: Remove stock from watchlist successfully (Happy Path)
    Given I am on the "watchlist" page
    And "AAPL" is currently in my watchlist
    When I press the "Remove" button next to "AAPL"
    Then I should see a "success" message
    And "AAPL" should be removed from my watchlist sidebar

  Scenario: : Add stock fails due to invalid ticker (Unhappy Path)
    Given I am on the watchlist management page
    When I attempt to add a stock with invalid ticker "XXXX"
    Then I should see an "invalid ticker" error message
    And "XXXX" should not be added to my watchlist