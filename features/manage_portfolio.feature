Feature: Manage Portfolio
  As a signed in user
  I want to create a portfolio and add stocks with quantities
  In order to view my holdings and their current calculated value.

  Background:
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the homepage

  Scenario: Add holding to portfolio successfully (Happy Path)
    Given I am on the "portfolio" page
    When I press the "Add Holding" button
    And I enter "AAPL" for the ticker and "10" for the quantity
    Then I should receive a "success" message
    And "AAPL" with quantity "10" and its calculated value should be visible in my portfolio

  Scenario: Add holding fails due to invalid inputs (Unhappy Path)
    Given I am on the "portfolio" page
    When I press the "Add Holding" button
    And I enter "INVALID123" for the ticker and "-5" for the quantity
    Then I should see an "invalid ticker or quantity" error message
    And no holding should be added to my portfolio

  Scenario: Market data provider unavailable for portfolio (Unhappy Path)
    Given I am on the "portfolio" page
    And the market data provider is temporarily unavailable
    When I add a holding "MSFT" with quantity "5"
    Then the holding "MSFT" is saved in my portfolio
    And I should see an "unavailable-data" message for its calculated value