Feature: Compare Two Stocks Side by Side
  As a user
  I want to compare two stocks side by side
  In order to understand the differences in risk, volatility, and long-term scenarios at a glance

  Background:
    Given I am on the homepage

  Scenario: Enable comparison and view side-by-side risk scores (Happy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I enable the "Compare two stocks" toggle
    And I enter "MSFT" as the second stock symbol
    Then I should see a side-by-side view of "AAPL" and "MSFT"
    And I should see a risk score for "AAPL"
    And I should see a risk score for "MSFT"

  Scenario: Enable comparison and view side-by-side scenario analysis (Happy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I enable the "Compare two stocks" toggle
    And I enter "TSLA" as the second stock symbol
    And I navigate to the "Scenario Analysis" section
    Then I should see a side-by-side view of "AAPL" and "TSLA"
    And I should see scenario data for "AAPL"
    And I should see scenario data for "TSLA"

  Scenario: Disable comparison toggle returns to single stock view (Unhappy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I enable the "Compare two stocks" toggle
    And I enter "MSFT" as the second stock symbol
    And I disable the "Compare two stocks" toggle
    Then I should see only the single stock view for "AAPL"

  Scenario: Second ticker left empty shows no comparison (Unhappy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I enable the "Compare two stocks" toggle
    And I leave the second stock symbol empty
    Then I should see only the single stock view for "AAPL"
