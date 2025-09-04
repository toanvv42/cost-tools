#!/usr/bin/env python3

from aws_cost_reporter import AWSCostReporter, ReportConfig, Granularity, GroupBy, FilterDimension
from datetime import datetime, timedelta

def example_rds_customer_report():
    """Example: RDS costs by usage type for specific customer"""
    reporter = AWSCostReporter()
    
    config = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01",
        linked_account_ids=["123456789012"],  # Replace with your account ID
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.USAGE_TYPE],
        filters={FilterDimension.SERVICE: ["Amazon Relational Database Service"]},
        tag_filters={"customer": ["CustomerName"]}  # Replace with your customer tag
    )
    
    print("Generating RDS customer report...")
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "rds_customer_costs.csv")
    print("Report saved to rds_customer_costs.csv")

def example_daily_ec2_costs():
    """Example: Daily EC2 costs by instance type"""
    reporter = AWSCostReporter()
    
    # Get last 7 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    config = ReportConfig(
        start_date=start_date,
        end_date=end_date,
        granularity=Granularity.DAILY,
        group_by=[GroupBy.INSTANCE_TYPE],
        filters={FilterDimension.SERVICE: ["Amazon Elastic Compute Cloud - Compute"]}
    )
    
    print("Generating daily EC2 costs...")
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "ec2_daily_costs.csv")
    print("Report saved to ec2_daily_costs.csv")

def example_multi_service_comparison():
    """Example: Compare costs across multiple services"""
    reporter = AWSCostReporter()
    
    config = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01",
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.SERVICE],
        filters={FilterDimension.SERVICE: [
            "Amazon Relational Database Service",
            "Amazon Elastic Compute Cloud - Compute", 
            "Amazon Simple Storage Service"
        ]}
    )
    
    print("Generating multi-service comparison...")
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "service_comparison.csv")
    print("Report saved to service_comparison.csv")

def example_regional_breakdown():
    """Example: Costs broken down by region"""
    reporter = AWSCostReporter()
    
    config = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01", 
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.SERVICE, GroupBy.REGION],
        linked_account_ids=["123456789012"]  # Replace with your account ID
    )
    
    print("Generating regional breakdown...")
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "regional_costs.csv")
    print("Report saved to regional_costs.csv")

def example_customer_tag_analysis():
    """Example: Analyze costs by customer tags"""
    reporter = AWSCostReporter()
    
    # First, get all customer tag values
    customers = reporter.get_tag_values("customer")
    print(f"Found customers: {customers}")
    
    # Generate report for all customers
    config = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01",
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.SERVICE],
        tag_filters={"customer": customers[:5]}  # Limit to first 5 customers
    )
    
    print("Generating customer analysis...")
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "customer_analysis.csv")
    print("Report saved to customer_analysis.csv")

def example_usage_type_deep_dive():
    """Example: Deep dive into usage types for a specific service"""
    reporter = AWSCostReporter()
    
    config = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01",
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.USAGE_TYPE, GroupBy.OPERATION],
        filters={FilterDimension.SERVICE: ["Amazon Relational Database Service"]},
        linked_account_ids=["123456789012"]  # Replace with your account ID
    )
    
    print("Generating usage type deep dive...")
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "rds_usage_deep_dive.csv")
    print("Report saved to rds_usage_deep_dive.csv")

def run_all_examples():
    """Run all example reports"""
    examples = [
        ("RDS Customer Report", example_rds_customer_report),
        ("Daily EC2 Costs", example_daily_ec2_costs), 
        ("Multi-Service Comparison", example_multi_service_comparison),
        ("Regional Breakdown", example_regional_breakdown),
        ("Customer Tag Analysis", example_customer_tag_analysis),
        ("Usage Type Deep Dive", example_usage_type_deep_dive)
    ]
    
    print("Running all example reports...")
    print("=" * 50)
    
    for name, func in examples:
        print(f"\n{name}:")
        print("-" * len(name))
        try:
            func()
        except Exception as e:
            print(f"Error: {e}")
            print("Note: Update account IDs and tag values for your environment")

if __name__ == "__main__":
    run_all_examples()