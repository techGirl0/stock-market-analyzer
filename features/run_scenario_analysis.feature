Feature: Run Long-Term Scenario Analysis
  As a user
  I want to run a long-term scenario analysis for a selected stock
  In order to understand what could happen to the price over 1, 3, and 5 years

  Background:
    Given I am on the homepage

  Scenario: Successfully view scenario analysis (Happy Path)
    Given I am on the "stock dashboard" page for "MSFT"
    When I navigate to the "Scenario Analysis" section
    Then I should see a loading indicator
    And I should see a worse case, middle case, and better case for 1 year
    And I should see a worse case, middle case, and better case for 3 years
    And I should see a worse case, middle case, and better case for 5 years
    And the worse case price should be lower than the middle case price
    And the middle case price should be lower than the better case price

  Scenario: Scenarios clearly labelled as not predictions (Unhappy Path)
    Given I am on the "stock dashboard" page for "MSFT"
    When I navigate to the "Scenario Analysis" section
    Then the scenarios should be labelled as illustrative "what if" cases
    And the section should include a disclaimer that these are not predictions or financial advice

  Scenario: Scenario analysis with insufficient data (Unhappy Path)
    Given I am on the "stock dashboard" page for "MSFT"
    And historical price data is unavailable
    When I navigate to the "Scenario Analysis" section
    Then I should see a message stating that not enough data is available to compute scenarios
