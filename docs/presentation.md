SLIDEs

Data Storyteller
Customer Ticket Journey
Customer Ticket Dashboard
Customer Ticket Q & A Agent
Signaling Trace Analyst
	Skill based Learning
FikraCore - Brain for Telecom Domain Knowledge 
FikraCore CLI check and validate the Knowledge Adaptation
FikraCore Ecosystem
	Operational Evidence 
	Correlation Layer
	Reasoning Enginer
	Hypotheses H1-H4
	Domain Attribution
	Validation - HITL
	FCAPS - Structured Learning
	


![alt text](image.png)

![alt text](image-1.png)

![alt text](image-2.png)

![alt text](image-3.png)

![alt text](image-4.png)

![alt text](image-5.png)

![alt text](image-6.png)

![alt text](image-7.png)

![alt text](image-8.png)

![alt text](image-9.png)

![alt text](image-10.png)

![alt text](image-11.png)

![alt text](image-12.png)

![alt text](image-13.png)

![alt text](image-14.png)

![alt text](image-15.png)

![alt text](image-16.png)

![alt text](image-17.png)

currently in POC i have:

Customer Ticket Dashboard

share the flow diagram  of what has been covered to pitch the idea

POC  covered:

1. **Customer Ticket Dashboard:** Centralized UI for ticket visibility.
2. **Customer Ticket Journey:** Visual tracking of end-to-end ticket progression.
3. **Incident StoryTeller:** Automatic generation of narrative context for incidents.
4. **Customer Trouble Ticket (TT) RAG Agent:** Interactive Q&A agent dedicated to handling trouble tickets.
5. **Trace Analyzer:** Dedicated component for processing and analyzing **Polystar Traces**.
6. **Interactive Voice Assistant:** Enables live voice interactions for both the Incident StoryTeller and Customer Ticket Journey.

**Backend Intelligent Agents**

- **StoryTeller Agent:** Directly traverses the **FikraCore TelcoBrain** backend to generate and narrate curated, context-aware incident stories.
- **Customer TT Q&A Agent:** Utilizes a hybrid data retrieval strategy:
  - **Chroma DB** serves as the vector database for tabular data ingestion and semantic search.
  - **PostgreSQL** retains the tabular data schema to enable precise, SQL-based structured data retrieval.
- **Signaling Analyst (Trace Analyzer Skill):** Visualizes end-to-end call flows, executes deep trace analysis, and extracts actionable troubleshooting insights.

**Voice Assistant Capabilities**

- **Incident Storytelling:** Synchronously displays the incident narrative retrieved from **FikraCore TelcoBrain** while playing the corresponding curated audio commentary.
- **Live Ticket Tracking:** Visually tracks the active ticket journey while generating real-time audio explanations of the ticket status and progress.


![alt text](image-18.png)

![alt text](image-19.png)


USE CASES


For management, I would not demonstrate three similar RCA cases. Use three scenarios that prove three different strengths of FikraCore:

Cross-domain reasoning
Knowledge-gap discovery + curated learning
Proactive what-if / resilience
That gives you a much stronger story than three fault-isolation demos.

Demo	Scenario	Domains	What it proves
1. Cross-Domain Service Outage	Transport degradation causes 5G/mobile-data impact while Core and RAN generate secondary alarms	Transport + Mobile Core + RAN	Correlation, causal reasoning, contradictions, blast radius

2. Prepaid Charging Failure	OCS/Diameter degradation causes intermittent session/charging failures after a recent change	IN/OCS + Mobile Core + Transport	Subscriber journey, signaling correlation, change relevance, knowledge-gap discovery, curated learning

3. Network Resilience What-if	What happens if a critical transport/RAN aggregation component fails?	RAN + Transport + Mobile Core + Services	H4 prediction, propagation, SPOF discovery, blast radius, mitigation comparison


![alt text](image-21.png)

![alt text](image-20.png)

![alt text](image-22.png)

![alt text](image-23.png)