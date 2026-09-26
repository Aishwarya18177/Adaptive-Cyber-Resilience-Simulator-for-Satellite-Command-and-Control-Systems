# Adaptive Cyber-Resilience Simulator for Satellite Command and Control Systems

## Overview

The **Adaptive Cyber-Resilience Simulator for Satellite Command and Control Systems** is a cybersecurity simulation platform that models a virtual satellite Command and Control (C2) environment.

The system allows controlled cyberattack scenarios to be simulated against the virtual satellite environment. It monitors telemetry, detects abnormal behaviour, determines the severity of the detected threat, and selects an appropriate response through a decision engine.

The main goal is to demonstrate **adaptive cyber-resilience** — responding to different levels of threats without unnecessarily disrupting critical satellite operations.

---

## Problem Statement

Satellite Command and Control systems depend on reliable communication between ground systems and spacecraft.

A cyberattack affecting communication or command channels can cause abnormal behaviour in telemetry and potentially disrupt operations.

A fixed response to every security incident may not always be appropriate. A low-severity event may only require an alert, while a more serious event may require stronger containment.

This project provides a controlled simulation environment to demonstrate the following security workflow:

**Detect → Assess → Decide → Respond → Recover**

---

## Objectives

- Simulate a virtual satellite Command and Control environment.
- Generate satellite telemetry data.
- Simulate controlled cyberattack scenarios.
- Detect abnormal telemetry behaviour.
- Identify the type of detected threat.
- Determine threat confidence and severity.
- Select an appropriate response using a decision engine.
- Demonstrate adaptive cyber-resilience.
- Monitor the complete process through a dashboard.
- Provide a safe environment for satellite cybersecurity experimentation.

---

## System Architecture

```text
                 ┌─────────────────────────┐
                 │   Satellite Simulator   │
                 │                         │
                 │  Telemetry Generation   │
                 │  Signal                 │
                 │  Uplink                 │
                 │  Downlink               │
                 │  Temperature            │
                 │  Battery                │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   Attack Simulation     │
                 │                         │
                 │ Controlled Attack       │
                 │ Scenarios               │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │    Detection Engine     │
                 │                         │
                 │ Telemetry Analysis      │
                 │ Threat Detection        │
                 │ Severity Assessment     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │    Decision Engine      │
                 │                         │
                 │ Threat + Severity       │
                 │         ↓               │
                 │ Response Selection      │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   Adaptive Response     │
                 │                         │
                 │ Alert / Throttle /      │
                 │ Isolate / Failover      │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │       Dashboard         │
                 │                         │
                 │ Telemetry               │
                 │ Threat Status           │
                 │ Detection Results       │
                 │ Response                │
                 └─────────────────────────┘

Project Workflow
Normal Satellite Operation
            ↓
      Telemetry Generation
            ↓
       Attack Simulation
            ↓
      Telemetry Changes
            ↓
       Threat Detection
            ↓
    Severity Assessment
            ↓
       Decision Engine
            ↓
     Adaptive Response
            ↓
      System Monitoring
            ↓
          Recovery
Main Components
1. Satellite Simulator

The satellite simulator creates a virtual satellite environment and generates telemetry representing the operational state of the simulated satellite.

The telemetry includes parameters such as:

Signal
Uplink
Downlink
Temperature
Battery

The simulator provides the baseline operational state used by the detection system.

2. Attack Simulation

The project provides a controlled environment for simulating cyberattack conditions.

The attacks are performed only against the virtual satellite environment.

The purpose is to introduce abnormal conditions into the telemetry so that the detection and response mechanisms can be evaluated safely.

Example:

Normal Telemetry
      ↓
Attack Condition Introduced
      ↓
Telemetry Behaviour Changes
      ↓
Detection Triggered
3. Detection Engine

The detection engine analyzes telemetry data and identifies abnormal behaviour.

It uses telemetry history and changes in system behaviour to determine whether suspicious activity is present.

The detector can provide:

Detection status
Attack type
Confidence
Severity
Detection reason

Example:

Detected: TRUE
Attack Type: JAMMING
Confidence: 100%
Severity: HIGH
4. Decision Engine

After a threat is detected, the decision engine determines an appropriate response.

The response depends on the detected threat and its severity.

Possible responses include:

Alert
Throttle
Isolate
Failover

Example decision flow:

Low Severity
     ↓
   ALERT

Medium Severity
     ↓
  THROTTLE

High Severity
     ↓
 ISOLATE / FAILOVER

The objective is to demonstrate an adaptive response rather than applying the same response to every detected event.

5. Dashboard

The dashboard provides a visual interface for monitoring the simulated satellite environment.

It can display:

Satellite status
Telemetry values
Threat status
Detected attack
Confidence
Severity
Selected response
System state

The dashboard makes the detection and response process visible during demonstrations.

Example Attack Scenario
Jamming Scenario

The system begins in normal operation.

Normal Operation
       ↓
Jamming Condition Introduced
       ↓
Signal Behaviour Changes
       ↓
Jamming Detected
       ↓
Severity Determined
       ↓
Adaptive Response Selected
       ↓
System Continues / Recovers

The change in telemetry and the resulting detection and response can be observed through the monitoring interface.

Project Structure
Satellite/
│
├── .gitignore
│
├── dashboard/
│   └── app.py
│
├── decision_engine/
│   ├── decision_engine.py
│   ├── live_decision.py
│   └── test_decision.py
│
├── detection/
│   ├── __init__.py
│   ├── detection_service.py
│   ├── detector.py
│   └── test_detector.py
│
├── metrics/
│   └── scenario_run.py
│
├── satellite/
│   └── simulator.py
│
└── telemetry
Technology Stack
Programming Language
Python
Backend and Simulation
FastAPI
Uvicorn
Dashboard
Streamlit
Development Environment
Visual Studio Code
Python Virtual Environment
Installation
1. Clone the repository
git clone https://github.com/Aishwarya18177/Adaptive-Cyber-Resilience-Simulator-for-Satellite-Command-and-Control-Systems.git
2. Navigate to the project
cd Adaptive-Cyber-Resilience-Simulator-for-Satellite-Command-and-Control-Systems
3. Create a virtual environment

Windows:

python -m venv .venv
4. Activate the virtual environment
.venv\Scripts\activate
5. Install project dependencies

If a requirements.txt file is provided:

pip install -r requirements.txt
Running the Project
Start the Satellite Simulator

From the project root:

python satellite/simulator.py
Start the Dashboard

Open another terminal and activate the virtual environment if required:

.venv\Scripts\activate

Then run:

streamlit run dashboard/app.py
Testing
Test the Detection Engine
python detection/test_detector.py
Test the Decision Engine
python decision_engine/test_decision.py

These tests help verify the individual detection and decision components.

Key Features
Virtual satellite environment
Satellite telemetry simulation
Controlled cyberattack simulation
Telemetry-based threat detection
Threat severity assessment
Detection confidence
Adaptive response selection
Real-time monitoring dashboard
Modular project architecture
Component-level testing
Safe cybersecurity simulation environment
Adaptive Cyber-Resilience

The main concept of this project is that different security events can require different responses.

Instead of using one fixed response for every event, the system evaluates the detected condition and selects a response.

                 Threat Detected
                       │
                       ▼
               Severity Assessment
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Low            Medium        High
          │            │            │
          ▼            ▼            ▼
        Alert       Throttle   Isolate/Failover

This approach demonstrates how a simulated Command and Control environment can adapt its response based on the detected security condition.

Why This Project?

Satellite systems are increasingly dependent on communication, telemetry, and command channels.

Cybersecurity monitoring for such environments requires more than simply detecting an abnormal event.

A resilient system should also be able to:

Detect abnormal behaviour.
Understand the potential severity.
Select an appropriate response.
Maintain essential functionality where possible.
Recover after the event.

This project demonstrates these concepts in a controlled simulation environment.

Project Scope

This project is a simulation-based cybersecurity prototype.

It does not connect to or control:

Real satellites
Real spacecraft
Operational satellite communication systems
Real Command and Control infrastructure

All attack scenarios and responses are performed within the simulated environment.

The project is intended for:

Cybersecurity education
Satellite cybersecurity research
Academic projects
Project demonstrations
Cyber-resilience experimentation
Future Enhancements

Possible future improvements include:

Additional attack scenarios
Advanced anomaly detection
Machine-learning-based detection
More detailed telemetry modelling
Improved recovery mechanisms
Historical attack and response analytics
Automated scenario evaluation
Extended dashboard visualizations
Performance and resilience metrics
Project Status

Status: Prototype / Demonstration

The project currently focuses on the integration of:

Satellite simulation
Telemetry generation
Threat detection
Threat severity assessment
Decision making
Adaptive response
Dashboard monitoring
Author

Aishwarya

Cybersecurity Project

Disclaimer

This project is a controlled cybersecurity simulation created for educational, research, and demonstration purposes.

It does not interact with real satellite systems, spacecraft, or operational Command and Control infrastructure.
