Feature: Search for a Stock
  As a user
  I want to search for a financial instrument by ticker or company name
  In order to view its market data, charts, and news.

  Background:
    Given I am on the homepage

  Scenario: Successful stock search (Happy Path)
    When I enter "AAPL" in the search field
    And I press the "search" button
    Then I should see "AAPL - Apple Inc." in the search results
    When I click on "AAPL - Apple Inc."
    Then I should see a loading indicator
    And I should be routed to the "stock dashboard" page for "AAPL"
    And I should see the current price, historical chart, and recent news

  Scenario: No search results found (Unhappy Path)
    When I enter "INVALIDTICKER123" in the search field
    And I press the "search" button
    Then I should receive an "empty state" message

  Scenario: Data unavailable due to provider down (Unhappy Path)
    When I enter "AAPL" in the search field
    And I press the "search" button
    And I click on "AAPL - Apple Inc."
    And the external provider is down
    Then I should receive an "unavailable-data" message on the dashboard