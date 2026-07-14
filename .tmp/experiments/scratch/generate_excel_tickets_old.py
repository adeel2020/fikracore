import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_raw_tickets():
    file_path = "/Users/adeelarshad/AgenticAIOPs/Complaint_managment_dashboard_old.xlsx"
    print(f"Generating synthetic raw ticket logs at {file_path}...")

    # Fix seed for reproducibility
    np.random.seed(42)
    random.seed(42)

    queues = ["CS", "PS", "IN", "VAS", "RAN", "IREG", "EI"]
    queue_weights = [0.25, 0.20, 0.18, 0.12, 0.10, 0.08, 0.07] # Matches NOC Ticket Share

    categories = ["MNP", "eSIM", "Data Bundle", "Roaming", "VoLTE"]
    countries = ["Saudi Arabia", "UK", "Germany", "US", "Singapore"]
    hotspots = ["Dubai Core", "Abu Dhabi Central", "Al Ain", "Sharjah / Ajman", "Fujairah East", "Ras Al Khaimah"]

    reassignments = ["IT", "SRO", "BSCS", "BLUE BSS", "IN"]
    reassignment_weights = [0.42, 0.21, 0.18, 0.12, 0.07]

    rejections = ["Missing Info", "Device", "Coverage", "Knowledge Gap (PP)", "BO Tool"]
    rejection_weights = [0.38, 0.24, 0.18, 0.13, 0.07]

    # Target compliance rates per Queue to make compliance data realistic
    # CS: 94%, PS: 72%, IN: 80%, VAS: 85%, RAN: 62%, IREG: 88%, EI: 91%
    compliance_targets = {
        "CS": 0.94, "PS": 0.72, "IN": 0.80, "VAS": 0.85, "RAN": 0.62, "IREG": 0.88, "EI": 0.91
    }

    tickets_list = []
    ticket_counter = 10001

    start_date = datetime(2025, 1, 1)

    # Generate 12 months (300 to 400 tickets per month)
    for month in range(1, 13):
        # Determine number of tickets for this month (random between 300 and 400)
        # Note: May: 312 tickets, Jun: 325, Dec: 300, Aug: 350 to align with previous totals
        if month == 1: num_tickets = 280
        elif month == 2: num_tickets = 260
        elif month == 3: num_tickets = 250
        elif month == 4: num_tickets = 290
        elif month == 5: num_tickets = 312
        elif month == 6: num_tickets = 325
        elif month == 7: num_tickets = 280
        elif month == 8: num_tickets = 350
        elif month == 9: num_tickets = 290
        elif month == 10: num_tickets = 340
        elif month == 11: num_tickets = 320
        elif month == 12: num_tickets = 300
        else: num_tickets = random.randint(300, 400)

        # Generate ticket dates within this month
        for _ in range(num_tickets):
            day = random.randint(1, 28) # Simple bound to avoid month-end overflows
            ticket_date = datetime(2025, month, day)

            # Assign Queue
            queue = np.random.choice(queues, p=queue_weights)

            # Assign Status: Resolved (70%), Reassigned (20%), Rejected (10%)
            status = np.random.choice(["Resolved", "Reassigned", "Rejected"], p=[0.70, 0.20, 0.10])

            # Assign Category
            category = random.choice(categories)

            # Assign Color Group: BLUE (60%), BROWN (40%)
            color_group = np.random.choice(["BLUE", "BROWN"], p=[0.60, 0.40])

            # Assign first response time based on compliance target
            target_compliance = compliance_targets[queue]
            met_sla = np.random.choice([True, False], p=[target_compliance, 1.0 - target_compliance])
            if met_sla:
                # Met SLA: response time <= 120 minutes (SLA is 2 hours)
                first_response = random.randint(10, 120)
            else:
                # Missed SLA: response time > 120 minutes
                first_response = random.randint(121, 240)

            # Assign reassignment / rejection fields depending on status
            reassigned_to = ""
            rejection_reason = ""
            if status == "Reassigned":
                reassigned_to = np.random.choice(reassignments, p=reassignment_weights)
            elif status == "Rejected":
                rejection_reason = np.random.choice(rejections, p=rejection_weights)

            # Roaming country
            country = random.choice(countries)

            # Regional hotspot name
            hotspot = random.choice(hotspots)

            tickets_list.append({
                "Ticket_ID": f"TK-{ticket_counter}",
                "Create_Date": ticket_date.strftime("%Y-%m-%d"),
                "Queue": queue,
                "Status": status,
                "Category": category,
                "Color_Group": color_group,
                "First_Response_Time_Mins": first_response,
                "Reassigned_To": reassigned_to,
                "Rejection_Reason": rejection_reason,
                "Country": country,
                "Hotspot_Name": hotspot
            })
            ticket_counter += 1

    # Save to single-sheet Excel
    df = pd.DataFrame(tickets_list)
    df.to_excel(file_path, sheet_name="Ticket_Logs", index=False)
    print(f"Generated {len(df)} tickets in {file_path} under 'Ticket_Logs' sheet.")

if __name__ == "__main__":
    generate_raw_tickets()
