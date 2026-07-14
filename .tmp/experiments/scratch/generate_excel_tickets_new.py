import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_raw_tickets():
    file_path = "/Users/adeelarshad/AgenticAIOPs/Complaint_managment_dashboard_new.xlsx"
    print(f"Generating synthetic raw ticket logs at {file_path}...")

    np.random.seed(42)
    random.seed(42)

    queues = ["CS", "PS", "IN", "VAS", "RAN", "IREG", "EI"]
    queue_weights = [0.261, 0.201, 0.171, 0.124, 0.101, 0.073, 0.069]

    categories = ["MNP", "eSIM", "Data Bundle", "Roaming", "VoLTE"]

    countries = ["UAE", "UK", "Germany", "US", "Singapore", "Saudi Arabia"]
    country_weights = [0.79, 0.044, 0.043, 0.042, 0.041, 0.040]

    reassignments = ["IT", "SRO", "BSCS", "BLUE BSS", "IN"]
    reassignment_weights = [0.42, 0.21, 0.18, 0.12, 0.07]

    reassignment_reasons_map = {
        "BLUE BSS": ["Bundle throttling", "Roaming bundle not active", "MNP definition mismatch", "VoLTE not active"],
        "BSCS":     ["data bundle not active", "Roaming bundle not active", "MNP definition mismatch", "VoLTE not active"],
        "IN":       ["MNP definition mismatch", "Bundle not active", "No Data allocation"],
        "IT":       ["IR Not Active", "PCF mismatch", "MNP definition mismatch", "eSIM not active", "VoLTE Tag issue"],
        "SRO":      ["MNP definition mismatch", "eSIM not active", "5GSA not aligned", "IR Not Active", "VoLTE Tag issue"],
    }

    rejections = ["Missing Info", "Device", "Coverage", "Knowledge Gap (PP)", "BO Tool"]
    rejection_weights = [0.38, 0.24, 0.18, 0.13, 0.07]

    compliance_targets = {
        "CS": 0.94, "PS": 0.72, "IN": 0.80, "VAS": 0.85, "RAN": 0.62, "IREG": 0.88, "EI": 0.91
    }

    tickets_list = []
    ticket_counter = 10001

    monthly_totals = [280, 260, 250, 290, 312, 325, 280, 350, 290, 340, 320, 300]

    for month in range(1, 13):
        num_tickets = monthly_totals[month - 1]

        for _ in range(num_tickets):
            day = random.randint(1, 28)
            ticket_date = datetime(2025, month, day)

            queue = np.random.choice(queues, p=queue_weights)
            status = np.random.choice(["Resolved", "Reassigned", "Rejected"], p=[0.69, 0.21, 0.10])
            category = random.choice(categories)
            color_group = np.random.choice(["BLUE", "BROWN"], p=[0.62, 0.38])

            target_compliance = compliance_targets[queue]
            met_sla = np.random.choice([True, False], p=[target_compliance, 1.0 - target_compliance])
            if met_sla:
                avg_time = random.randint(10, 120)
            else:
                avg_time = random.randint(121, 240)

            reassigned_to = None
            rejection_reason = None
            reassignment_reason = None

            if status == "Reassigned":
                reassigned_to = np.random.choice(reassignments, p=reassignment_weights)
                reasons = reassignment_reasons_map.get(reassigned_to, ["MNP definition mismatch"])
                reassignment_reason = random.choice(reasons)
            elif status == "Rejected":
                rejection_reason = np.random.choice(rejections, p=rejection_weights)

            country = np.random.choice(countries, p=country_weights)

            tickets_list.append({
                "Ticket_ID": f"TK-{ticket_counter}",
                "Create_Date": ticket_date.strftime("%Y-%m-%d"),
                "Ticket Queue": queue,
                "Ticket Status": status,
                "Issue Category": category,
                "Reassignment Reason": reassignment_reason,
                "Color_Group": color_group,
                "Average_Time_spent_in_Mins": avg_time,
                "Reassigned_To": reassigned_to,
                "Rejection_Reason": rejection_reason,
                "Country": country,
            })
            ticket_counter += 1

    df = pd.DataFrame(tickets_list)
    df.to_excel(file_path, sheet_name="Ticket_Logs", index=False)
    print(f"Generated {len(df)} tickets in {file_path} under 'Ticket_Logs' sheet.")

if __name__ == "__main__":
    generate_raw_tickets()
