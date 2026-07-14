import pandas as pd
import os

def generate_template():
    # File Path
    file_path = "/Users/adeelarshad/AgenticAIOPs/Operations_Dashboard_Data_Template.xlsx"
    
    # 1. Monthly Ticket Distribution
    df_monthly = pd.DataFrame([
        {"Month": "Jan", "BLUE_Tickets": 170, "BROWN_Tickets": 110},
        {"Month": "Feb", "BLUE_Tickets": 145, "BROWN_Tickets": 115},
        {"Month": "Mar", "BLUE_Tickets": 135, "BROWN_Tickets": 115},
        {"Month": "Apr", "BLUE_Tickets": 195, "BROWN_Tickets": 95},
        {"Month": "May", "BLUE_Tickets": 234, "BROWN_Tickets": 78},
        {"Month": "Jun", "BLUE_Tickets": 260, "BROWN_Tickets": 65},
        {"Month": "Jul", "BLUE_Tickets": 175, "BROWN_Tickets": 105},
        {"Month": "Aug", "BLUE_Tickets": 245, "BROWN_Tickets": 105},
        {"Month": "Sep", "BLUE_Tickets": 180, "BROWN_Tickets": 110},
        {"Month": "Oct", "BLUE_Tickets": 255, "BROWN_Tickets": 85},
        {"Month": "Nov", "BLUE_Tickets": 256, "BROWN_Tickets": 64},
        {"Month": "Dec", "BLUE_Tickets": 210, "BROWN_Tickets": 90}
    ])

    # 2. NOC Avg Queue Times
    df_queue_times = pd.DataFrame([
        {"Queue_Name": "CS Queue", "Closed_Tickets": 34, "Total_Tickets": 52, "Avg_Time_Mins": 45, "SLA_Compliance_Pct": 94},
        {"Queue_Name": "PS Queue", "Closed_Tickets": 32, "Total_Tickets": 62, "Avg_Time_Mins": 135, "SLA_Compliance_Pct": 72},
        {"Queue_Name": "IN Queue", "Closed_Tickets": 24, "Total_Tickets": 24, "Avg_Time_Mins": 72, "SLA_Compliance_Pct": 80},
        {"Queue_Name": "VAS Queue", "Closed_Tickets": 23, "Total_Tickets": 24, "Avg_Time_Mins": 80, "SLA_Compliance_Pct": 85},
        {"Queue_Name": "RAN Queue", "Closed_Tickets": 18, "Total_Tickets": 22, "Avg_Time_Mins": 142, "SLA_Compliance_Pct": 62},
        {"Queue_Name": "IREG Queue", "Closed_Tickets": 18, "Total_Tickets": 22, "Avg_Time_Mins": 90, "SLA_Compliance_Pct": 88},
        {"Queue_Name": "EI Queue", "Closed_Tickets": 15, "Total_Tickets": 18, "Avg_Time_Mins": 55, "SLA_Compliance_Pct": 91}
    ])

    # 3. First Response Issues
    df_issues = pd.DataFrame([
        {"Issue_Category": "MNP", "Tickets": 121, "Met_SLA_Pct": 12, "Avg_Time_Mins": 60},
        {"Issue_Category": "eSIM", "Tickets": 85, "Met_SLA_Pct": 65, "Avg_Time_Mins": 43},
        {"Issue_Category": "Data Bundle", "Tickets": 85, "Met_SLA_Pct": 75, "Avg_Time_Mins": 32},
        {"Issue_Category": "Roaming", "Tickets": 74, "Met_SLA_Pct": 90, "Avg_Time_Mins": 29},
        {"Issue_Category": "VoLTE", "Tickets": 64, "Met_SLA_Pct": 30, "Avg_Time_Mins": 19}
    ])

    # 4. Weekly Complaint Volume
    df_weekly = pd.DataFrame([
        {"Day": "Monday", "BROWN_Tickets": 245, "BLUE_Tickets": 180},
        {"Day": "Tuesday", "BROWN_Tickets": 190, "BLUE_Tickets": 215},
        {"Day": "Wednesday", "BROWN_Tickets": 280, "BLUE_Tickets": 140},
        {"Day": "Thursday", "BROWN_Tickets": 210, "BLUE_Tickets": 230},
        {"Day": "Friday", "BROWN_Tickets": 340, "BLUE_Tickets": 290},
        {"Day": "Saturday", "BROWN_Tickets": 160, "BLUE_Tickets": 195},
        {"Day": "Sunday", "BROWN_Tickets": 120, "BLUE_Tickets": 145}
    ])

    # 5. Trouble Tickets 30 Days
    df_tt_30d = pd.DataFrame([
        {"Date": "Day 3", "Resolved": 85, "Reassigned": 18, "Rejected": 8, "SLA_Compliance_Rate_Pct": 91.2},
        {"Date": "Day 6", "Resolved": 92, "Reassigned": 20, "Rejected": 10, "SLA_Compliance_Rate_Pct": 90.1},
        {"Date": "Day 9", "Resolved": 110, "Reassigned": 25, "Rejected": 12, "SLA_Compliance_Rate_Pct": 89.8},
        {"Date": "Day 12", "Resolved": 98, "Reassigned": 15, "Rejected": 7, "SLA_Compliance_Rate_Pct": 93.4},
        {"Date": "Day 15", "Resolved": 115, "Reassigned": 30, "Rejected": 15, "SLA_Compliance_Rate_Pct": 87.5},
        {"Date": "Day 18", "Resolved": 120, "Reassigned": 22, "Rejected": 9, "SLA_Compliance_Rate_Pct": 91.5},
        {"Date": "Day 21", "Resolved": 105, "Reassigned": 19, "Rejected": 11, "SLA_Compliance_Rate_Pct": 90.2},
        {"Date": "Day 24", "Resolved": 130, "Reassigned": 28, "Rejected": 14, "SLA_Compliance_Rate_Pct": 89.6},
        {"Date": "Day 27", "Resolved": 140, "Reassigned": 20, "Rejected": 8, "SLA_Compliance_Rate_Pct": 94.1},
        {"Date": "Day 30", "Resolved": 125, "Reassigned": 17, "Rejected": 6, "SLA_Compliance_Rate_Pct": 95.2}
    ])

    # 6. Reassignments and Rejection Reasons
    df_reassignments_rejections = pd.DataFrame([
        {"Metric_Type": "Reassignment", "Name": "IT", "Tickets_Count": 42},
        {"Metric_Type": "Reassignment", "Name": "SRO", "Tickets_Count": 21},
        {"Metric_Type": "Reassignment", "Name": "BSCS", "Tickets_Count": 18},
        {"Metric_Type": "Reassignment", "Name": "BLUE BSS", "Tickets_Count": 12},
        {"Metric_Type": "Reassignment", "Name": "IN", "Tickets_Count": 7},
        {"Metric_Type": "Rejection_Reason", "Name": "Missing Info", "Tickets_Count": 192},
        {"Metric_Type": "Rejection_Reason", "Name": "Device", "Tickets_Count": 122},
        {"Metric_Type": "Rejection_Reason", "Name": "Coverage", "Tickets_Count": 91},
        {"Metric_Type": "Rejection_Reason", "Name": "Knowledge Gap (PP)", "Tickets_Count": 67},
        {"Metric_Type": "Rejection_Reason", "Name": "BO Tool", "Tickets_Count": 34}
    ])

    # 7. Roaming Complaints by Countries
    df_roaming_countries = pd.DataFrame([
        {"Date": "Aug 1", "SaudiArabia": 120, "UK": 95, "Germany": 45, "US": 154, "Singapore": 80},
        {"Date": "Aug 3", "SaudiArabia": 140, "UK": 120, "Germany": 65, "US": 120, "Singapore": 95},
        {"Date": "Aug 5", "SaudiArabia": 110, "UK": 220, "Germany": 90, "US": 110, "Singapore": 75},
        {"Date": "Aug 7", "SaudiArabia": 240, "UK": 190, "Germany": 75, "US": 190, "Singapore": 130},
        {"Date": "Aug 9", "SaudiArabia": 180, "UK": 140, "Germany": 120, "US": 140, "Singapore": 115},
        {"Date": "Aug 11", "SaudiArabia": 160, "UK": 130, "Germany": 110, "US": 220, "Singapore": 110},
        {"Date": "Aug 13", "SaudiArabia": 210, "UK": 165, "Germany": 85, "US": 130, "Singapore": 90},
        {"Date": "Aug 15", "SaudiArabia": 195, "UK": 150, "Germany": 95, "US": 145, "Singapore": 85}
    ])

    # 8. NOC Tickets Distribution (CS, PS, IN, etc.)
    df_noc_dist = pd.DataFrame([
        {"Queue": "CS", "Value": 312, "Percentage": 25},
        {"Queue": "PS", "Value": 250, "Percentage": 20},
        {"Queue": "IN", "Value": 225, "Percentage": 18},
        {"Queue": "VAS", "Value": 150, "Percentage": 12},
        {"Queue": "RAN", "Value": 125, "Percentage": 10},
        {"Queue": "IREG", "Value": 100, "Percentage": 8},
        {"Queue": "EI", "Value": 88, "Percentage": 7}
    ])

    # 9. UAE Regional Hotspots
    df_uae_hotspots = pd.DataFrame([
        {"Hotspot_Name": "Dubai Core", "Tickets_Count": 142},
        {"Hotspot_Name": "Abu Dhabi Central", "Tickets_Count": 210},
        {"Hotspot_Name": "Al Ain", "Tickets_Count": 88},
        {"Hotspot_Name": "Sharjah / Ajman", "Tickets_Count": 122},
        {"Hotspot_Name": "Fujairah East", "Tickets_Count": 54},
        {"Hotspot_Name": "Ras Al Khaimah", "Tickets_Count": 42}
    ])

    # Write to Excel
    print(f"Creating Excel template at {file_path}...")
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df_monthly.to_excel(writer, sheet_name="Monthly_Distribution", index=False)
        df_queue_times.to_excel(writer, sheet_name="NOC_Queue_Times", index=False)
        df_issues.to_excel(writer, sheet_name="First_Response_Issues", index=False)
        df_weekly.to_excel(writer, sheet_name="Weekly_Volume", index=False)
        df_tt_30d.to_excel(writer, sheet_name="Trouble_Tickets_30d", index=False)
        df_reassignments_rejections.to_excel(writer, sheet_name="Reassignments_Rejections", index=False)
        df_roaming_countries.to_excel(writer, sheet_name="Roaming_By_Country", index=False)
        df_noc_dist.to_excel(writer, sheet_name="NOC_Tickets_Distribution", index=False)
        df_uae_hotspots.to_excel(writer, sheet_name="UAE_Regional_Hotspots", index=False)
    
    print("Excel template generated successfully!")

if __name__ == "__main__":
    generate_template()
