Feature: Generate Research Brief
  As a user
  I want to generate a structured research brief for a specific stock
  In order to view a consolidated summary of its market snapshot, risk, and forecasts.

  Background:
    Given I am on the homepage

  Scenario: Successfully generate research brief (Happy Path)
    Given I am on the "stock dashboard" page for "NVDA"
    When I press the "Generate Brief" button
    Then I should see a loading indicator
    And the system compiles data and generates the brief
    And I should see the "structured research brief" section
    And I should see data sources and timestamps attached to the analysis
    And the brief includes a disclaimer regarding investment advice

  Scenario: Incomplete data for brief (Unhappy Path)
    Given I am on the "stock dashboard" page for "NVDA"
    And historical forecast data is partially unavailable
    When I press the "Generate Brief" button
    Then I should see the "structured research brief" section
    And I should see a clear note stating which data was unavailable

  Scenario: Refuse personalized investment advice (Unhappy Path)
    Given I am on the "stock dashboard" page for "NVDA"
    When I submit a prompt asking "Should I buy NVDA right now?"
    Then the system refuses to provide a personalized buy or sell recommendation
    And the system displays the compliance disclaimer
