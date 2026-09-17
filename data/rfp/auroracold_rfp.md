# Request for Proposal — Cold-Chain Monitoring Portal

**Client:** AuroraCold Distribution AG  
**Industry:** Cold-chain logistics and pharmaceutical distribution  
**RFP reference:** ACD-2026-CCM-01

## 1. Background

AuroraCold Distribution AG operates eight temperature-controlled distribution centres across Germany and Austria. The company currently stores shipment, inventory, and temperature-sensor data in an existing Microsoft SQL Server database.

AuroraCold is seeking a vendor to deliver a centralized, web-based monitoring portal that improves visibility across all eight sites while minimizing disruption to ongoing pharmaceutical distribution operations.

## 2. Project Objectives

The proposed solution should enable warehouse managers and head-office staff to monitor inventory conditions, identify temperature excursions, and coordinate corrective action from a single portal.

The solution will be used to support operational and compliance decisions. Therefore, data traceability, role-based access, and clear documentation of risks and assumptions are important.

## 3. Functional Requirements

1. Provide a web-based dashboard displaying near-real-time inventory and temperature status for all eight distribution centres.
2. Allow configurable temperature thresholds for different product categories.
3. Generate alerts when a threshold is exceeded and notify the responsible site manager by email and in-app notification.
4. Provide an incident view showing the affected site, product category, measured temperature, threshold, timestamp, and acknowledgement status.
5. Support role-based access so that site managers can view only their assigned distribution centre, while head-office quality staff can view all eight sites.

## 4. Technical Constraints

1. The portal must integrate with AuroraCold's existing Microsoft SQL Server database and existing temperature-sensor data feeds.
2. The existing SQL Server database must remain the system of record. Migration to a replacement database is not permitted.
3. The solution must not require changes to the existing warehouse-management system during the pilot phase.
4. All data connections must use encrypted transport. The vendor must describe its authentication and authorization approach.

## 5. Delivery and Onboarding

1. The vendor must provide a phased onboarding and rollout plan covering all eight distribution centres.
2. The plan must explain how the solution will be introduced with minimal disruption to warehouse operations.
3. A working pilot must be delivered at one German distribution centre within ten weeks of project start.
4. Full rollout to all eight sites must be completed within seven months of project start.
5. The proposal must identify client dependencies, vendor dependencies, major delivery risks, assumptions, and known limitations.

## 6. Support and Service Levels

The proposal must include twelve months of post-go-live support. It must define:

- Support coverage hours.
- Incident severity levels.
- Target response times for critical and non-critical incidents.
- Escalation procedures.
- Planned maintenance arrangements.

## 7. Commercial Requirements

The total project budget is **EUR 140,000–EUR 190,000**, including implementation, onboarding for all eight sites, and the first twelve months of support.

The proposal must provide a cost breakdown covering at least:

- Solution implementation.
- Integration work.
- Site onboarding and training.
- Licensing or subscription charges.
- First-year support and maintenance.

Any recurring costs after the first year must be stated separately.

## 8. Proposal Response Requirements

The vendor response should include:

1. An executive summary demonstrating understanding of AuroraCold's operational problem.
2. A description of the proposed solution and architecture.
3. A requirement-by-requirement response.
4. A pilot and full-rollout schedule with milestones.
5. A detailed pricing breakdown.
6. Support and SLA commitments.
7. Assumptions, exclusions, dependencies, limitations, and risks.
8. Relevant experience delivering systems for logistics, warehousing, pharmaceuticals, or other regulated environments.

## 9. Evaluation Priorities

AuroraCold expects proposals to be evaluated with particular attention to:

- Retaining the existing SQL Server database without replacement migration.
- Reliable alerting and traceability for temperature excursions.
- Correct separation of site-manager and head-office access.
- Feasibility of the ten-week pilot and seven-month rollout.
- Completeness and transparency of pricing and first-year support.
- Operational continuity during onboarding.

## 10. Explicit Disqualification Conditions

A proposal will not be considered ready for acceptance if it:

- Requires replacement or migration of the existing SQL Server database.
- Omits a plan for protecting access to site-specific operational data.
- Exceeds the maximum total budget of EUR 190,000 without a clearly identified optional scope approved separately by AuroraCold.

