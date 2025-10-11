# 6_1_Loan_Navigator_Agent

# Loan Navigator Agent Suite  
### *AI-Powered Multi-Agent Support System for Fintech Loan Operations*

**Loan Navigator Agent Suite** is an **agentic AI application** built for *BlueLoans4all*, a micro-lending fintech platform, to automate and streamline customer loan support queries.  
Powered by **Google Vertex AI (Gemini Models)** and orchestrated using **LangGraph**, the system simulates an intelligent financial support desk that answers EMI, prepayment, and policy-related questions—accurately, securely, and in real-time.

---
## Overview

In India’s fast-growing fintech ecosystem, support centers face repetitive and compliance-critical loan queries.  
This project introduces a **multi-agent AI system** that combines **natural language understanding**, **retrieval-augmented generation (RAG)**, and **financial simulation** capabilities — hosted and monitored entirely on **Google Cloud Platform (GCP)**.

---

## Key Features

| Agent | Role | Core Function |
|--------|------|----------------|
|**Supervisor Agent** | Orchestrator | Classifies intent, routes queries, merges results |
|**SQL Analyst Agent** | Data Retrieval | Converts NL → SQL and fetches loan data securely |
|**Policy Guru Agent** | Compliance/RAG | Retrieves RBI & internal policy info with citations |
|**What-If Calculator Agent** | Simulation | Runs EMI & prepayment scenario calculations |

---

## System Architecture

            +----------------+
            |   User Query   |
            +-------+--------+
                    |
                    v
    +-----------------------------------------+
    |             SupervisorAgent             |
    +-----------------------------------------+
    |                 |                |
    v                 v                v
    +-----------+ +-----------+ +-----------------+
    | SQLAgent | | PolicyGuru| | WhatIfCalculator|
    +-----------+ +-----------+ +-----------------+
            \         |           /
             \        |          /
              v       v         v
            +-------------------+
            | Response Synthesis|
            +-------------------+
                      |
                      v
                +----------------+
                | Final Answer   |
                +----------------+

---

## Cloud-Native Stack

- **Cloud Platform:** Google Cloud Platform (GCP)  
- **AI Service:** Vertex AI (Gemini Models)  
- **Agent Framework:** LangGraph / CrewAI  
- **Vector DB:** Chroma / Pinecone  
- **Backend:** FastAPI  
- **Deployment:** Docker + Cloud Run + Artifact Registry  
- **Monitoring:** Google Cloud Operations Suite, Langfuse / MLflow  
- **Secrets:** Google Secret Manager  
- **Database:** SQLite (Loan data)

---

## Core Capabilities

- **Natural Language to SQL** – Converts customer questions like *“What’s my next EMI?”* into parameterized SQL queries.
- **RAG-based Policy Lookup** – Fetches and cites RBI guidelines or internal policies from a vector DB.
- **What-if Simulations** – Computes prepayment, tenure change, and EMI adjustments dynamically.
- **Autonomous Orchestration** – Supervisor coordinates multiple agents to deliver unified, compliant answers.
- **Audit & Traceability** – All interactions logged via Langfuse/MLflow for transparency and compliance.

---

## Deployment

### 1. Build Container

```bash
docker build -t loan-navigator .
```

### 2. Push to Artifact Registry

``` bash
gcloud builds submit --tag gcr.io/PROJECT_ID/loan-navigator
```

### 3. Deploy to Cloud Run

``` bash
gcloud run deploy loan-navigator \
  --image gcr.io/PROJECT_ID/loan-navigator \
  --platform managed \
  --allow-unauthenticated
```

## API Endpoint

POST /ask

### Request:

``` json
{ "query": "Can I prepay my loan early?" }
```

### Response:

``` json
{
  "response": {
    "answer": "Yes, your loan is eligible for prepayment with no penalties as per policy 4.3.1.",
    "citations": ["policy_loan_prepayment.pdf#page=3"]
  }
}
```

## Monitoring & Feedback Loop

- **Langfuse**: Tracks LLM token usage, latency, and fallback triggers.
- **MLflow**: Logs versioned model usage and prompt performance.
- **Google Cloud Operations Suite**: Dashboards for Cloud Run metrics, logs, and alerts.

## Deliverables

- Containerized multi-agent app deployed on Cloud Run
- Secure API endpoints (FastAPI + OpenAPI spec)
- LangGraph-based agent orchestration flow
- Pre-configured monitoring dashboard
- Setup and governance runbook

## Future Enhancements

- Add user authentication (OAuth 2.0 / IAP)
- Enable multilingual support (English, Hindi, Tamil)
- Fine-tune Gemini models for loan-specific context
- Integrate voice-based query input

## Maintainers

- **Capstone Team** – 
- **Tech Stack**: Python · Vertex AI · LangGraph · ChromaDB · FastAPI · GCP Cloud Run
