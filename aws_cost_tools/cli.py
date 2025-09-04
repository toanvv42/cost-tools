#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional

from .reporter import (
    AWSCostReporter,
    FilterDimension,
    Granularity,
    GroupBy,
    ReportConfig,
)


def parse_date(date_str: str) -> str:
    """Parse date string in various formats"""
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def parse_group_by(group_by_str: Optional[str]):
    """Parse comma-separated group by options"""
    if not group_by_str:
        return []

    valid_options = {g.name.lower(): g for g in GroupBy}
    groups = []

    for group in group_by_str.lower().split(","):
        group = group.strip()
        if group in valid_options:
            groups.append(valid_options[group])
        else:
            available = ", ".join(valid_options.keys())
            raise ValueError(f"Invalid group by option: {group}. Available: {available}")

    return groups


def parse_filters(filter_str: Optional[str]):
    """Parse filter string in format key1=val1,val2;key2=val3"""
    if not filter_str:
        return None, None

    dimension_filters: dict = {}
    tag_filters: dict = {}

    for filter_pair in filter_str.split(";"):
        if "=" not in filter_pair:
            continue

        key, values = filter_pair.split("=", 1)
        key = key.strip()
        value_list = [v.strip() for v in values.split(",")]

        # Check if it's a dimension filter
        dimension_key = None
        for dim in FilterDimension:
            if dim.name.lower() == key.lower():
                dimension_key = dim
                break

        if dimension_key:
            dimension_filters[dimension_key] = value_list
        else:
            # Treat as tag filter
            tag_filters[key] = value_list

    return dimension_filters if dimension_filters else None, tag_filters if tag_filters else None


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate AWS cost reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
Examples:
  # RDS costs for last 30 days by usage type
  %(prog)s --service rds --days 30 --group-by usage_type

  # EC2 costs by instance type for specific account
  %(prog)s --service ec2 --account 123456789012 --group-by instance_type

  # Daily costs for last week
  %(prog)s --days 7 --granularity daily --group-by service

  # Filter by customer tag
  %(prog)s --filters "customer=CustomerA,CustomerB" --group-by service

  # Multiple filters and groupings
  %(prog)s --filters "service=Amazon Relational Database Service;customer=CustomerA" \
           --group-by usage_type,region --granularity daily --days 7

Available services (common):
  - rds (Amazon Relational Database Service)
  - ec2 (Amazon Elastic Compute Cloud - Compute)
  - s3 (Amazon Simple Storage Service)
  - lambda (AWS Lambda)

Available group by options:
  service, usage_type, instance_type, region, availability_zone,
  operation, purchase_type, platform, tenancy
        """,
    )

    # Time range options (mutually exclusive)
    time_group = parser.add_mutually_exclusive_group(required=True)
    time_group.add_argument("--days", type=int, help="Number of days back from today")
    time_group.add_argument(
        "--date-range", nargs=2, metavar=("START", "END"), help="Start and end dates (YYYY-MM-DD)"
    )

    # Basic options
    parser.add_argument("--account", "--linked-account", help="Linked account ID")
    parser.add_argument(
        "--accounts",
        "--linked-accounts",
        help="Comma-separated linked account IDs",
    )
    parser.add_argument(
        "--granularity",
        choices=["daily", "monthly", "hourly"],
        default="monthly",
        help="Report granularity",
    )
    parser.add_argument("--group-by", help="Comma-separated group by options")
    parser.add_argument(
        "--service", help="Service shortname (rds, ec2, s3, lambda) or full name"
    )
    parser.add_argument("--filters", help="Filters in format: key1=val1,val2;key2=val3")

    # Output options
    parser.add_argument("--output", "-o", default="cost_report.csv", help="Output CSV file")
    parser.add_argument("--profile", help="AWS profile name")

    # Utility options
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="List available linked accounts",
    )
    parser.add_argument(
        "--list-services",
        action="store_true",
        help="List available services",
    )
    parser.add_argument(
        "--list-customers",
        action="store_true",
        help="List available customer tag values",
    )

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    reporter = AWSCostReporter(profile_name=args.profile)

    # Handle utility options
    if args.list_accounts:
        accounts = reporter.get_linked_accounts()
        print("Available Linked Accounts:")
        for account_id, name in accounts.items():
            print(f"  {account_id}: {name}")
        return

    if args.list_services:
        services = reporter.get_services()
        print("Available Services:")
        for service in sorted(services):
            print(f"  {service}")
        return

    if args.list_customers:
        try:
            customers = reporter.get_tag_values("customer")
            print("Available Customer Tags:")
            for customer in sorted(customers):
                print(f"  {customer}")
        except Exception as e:
            print(f"Error retrieving customer tags: {e}")
        return

    # Build time range
    if args.days:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    else:
        start_date = parse_date(args.date_range[0])
        end_date = parse_date(args.date_range[1])

    # Build linked accounts list
    linked_accounts = None
    if args.account:
        linked_accounts = [args.account]
    elif args.accounts:
        linked_accounts = [acc.strip() for acc in args.accounts.split(",")]

    # Parse granularity
    granularity = Granularity(args.granularity.upper())

    # Parse group by
    group_by = parse_group_by(args.group_by)

    # Parse filters
    dimension_filters, tag_filters = parse_filters(args.filters)

    # Handle service shorthand
    if args.service:
        service_map = {
            "rds": "Amazon Relational Database Service",
            "ec2": "Amazon Elastic Compute Cloud - Compute",
            "s3": "Amazon Simple Storage Service",
            "lambda": "AWS Lambda",
        }

        if args.service.lower() in service_map:
            service_name = service_map[args.service.lower()]
        else:
            service_name = args.service

        if not dimension_filters:
            dimension_filters = {}
        dimension_filters[FilterDimension.SERVICE] = [service_name]

    # Create config
    config = ReportConfig(
        start_date=start_date,
        end_date=end_date,
        linked_account_ids=linked_accounts,
        granularity=granularity,
        group_by=group_by,
        filters=dimension_filters,
        tag_filters=tag_filters,
    )

    # Generate and export report
    try:
        print(f"Generating report from {start_date} to {end_date}...")
        data = reporter.generate_report(config)
        reporter.export_to_csv(data, args.output)
        print(f"Report saved to: {args.output}")

        # Show summary
        if data.get("ResultsByTime"):
            total_results = len(data["ResultsByTime"])
            total_groups = sum(len(r.get("Groups", [])) for r in data["ResultsByTime"])
            print(f"Summary: {total_results} time periods, {total_groups} total data points")

    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
