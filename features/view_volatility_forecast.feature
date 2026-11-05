Feature: View Volatility Forecast
  As a user
  I want to view a volatility forecast for a selected stock
  In order to understand how much the price might move in the coming days

  Background:
    Given I am on the homepage

  Scenario: Successfully view volatility forecast (Happy Path)
    Given I am on the "stock dashboard" page for "TSLA"
    When I navigate to the "Volatility Forecast" section
    Then I should see a loading indicator
    And I should see expected price movement ranges for 5, 10, and 20 days
    And each range should be shown as a percentage and a dollar amount
    And the section should explain what volatility means in plain English

  Scenario: Insufficient price history (Unhappy Path)
    Given I am on the "stock dashboard" page for "TSLA"
    And the stock has less than 21 days of price history available
    When I navigate to the "Volatility Forecast" section
    Then I should see a message stating that not enough data is available
    And no forecast numbers should be displayed

  Scenario: Forecast shown as range not prediction (Unhappy Path)
    Given I am on the "stock dashboard" page for "TSLA"
    When I navigate to the "Volatility Forecast" section
    Then the forecast should be labelled as a statistical range
    And the section should include a disclaimer that this is not a prediction
