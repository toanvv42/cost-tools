# AWS Cost Reporting Tool

A flexible Python framework for generating AWS cost reports with CSV export capabilities.

## Features

- ✅ **Choose linked account ID**: Filter by specific AWS accounts
- ✅ **Time range**: Flexible date ranges (days back or specific dates)  
- ✅ **Granularity**: Daily, monthly, or hourly breakdowns
- ✅ **Group by**: Multiple grouping options (service, usage type, region, etc.)
- ✅ **Filter by**: Services, tags, dimensions
- ✅ **CSV export**: Clean CSV output for analysis
- ✅ **Extensible**: Easy to add new report types

## Quick Start

### Installation

Using uv (recommended):

```bash
uv venv
source .venv/bin/activate
uv sync
```

Alternative with pip:

```bash
pip install boto3
```

### Basic Usage

```bash
# RDS costs for last 30 days
uv run cost-tools --service rds --days 30 --group-by usage_type

# EC2 costs by instance type for specific account  
uv run cost-tools --service ec2 --account 123456789012 --group-by instance_type

# Daily costs for last week
uv run cost-tools --days 7 --granularity daily --group-by service
```

## CLI Reference

### Time Range (required, pick one)
- `--days N`: N days back from today
- `--date-range START END`: Specific date range (YYYY-MM-DD)

### Filtering Options
- `--account ID`: Single linked account ID
- `--accounts ID1,ID2`: Multiple linked account IDs
- `--service NAME`: Service (rds, ec2, s3, lambda, or full name)
- `--filters "key=val1,val2;key2=val3"`: Advanced filtering

### Grouping and Output
- `--group-by OPTIONS`: Comma-separated grouping (service, usage_type, region, etc.)
- `--granularity LEVEL`: daily, monthly, or hourly
- `--output FILE`: Output CSV file (default: cost_report.csv)
- `--profile PROFILE`: AWS profile name

### Utility Commands
- `--list-accounts`: Show available linked accounts
- `--list-services`: Show available services  
- `--list-customers`: Show customer tag values

## Examples

Tip: You can run all packaged examples to generate sample reports (update account IDs and tag values in your environment first):

```bash
uv run cost-tools-examples
```

### Your Original Requirement
```bash
# RDS costs by usage type, filtered by customer tag and account
uv run cost-tools \
  --service rds \
  --account 123456789012 \
  --filters "customer=CustomerName" \
  --group-by usage_type \
  --days 30
```

### More Examples
```bash
# Multi-service comparison
uv run cost-tools \
  --filters "service=Amazon Relational Database Service,Amazon Elastic Compute Cloud - Compute" \
  --group-by service \
  --days 30

# Regional breakdown with daily granularity
uv run cost-tools \
  --service ec2 \
  --group-by region \
  --granularity daily \
  --days 7

# Multiple customers and services
uv run cost-tools \
  --filters "customer=CustomerA,CustomerB;service=Amazon Relational Database Service" \
  --group-by usage_type \
  --days 30
```

## Programmatic Usage

```python
from aws_cost_tools import AWSCostReporter, ReportConfig, Granularity, GroupBy, FilterDimension

# Create reporter
reporter = AWSCostReporter()

# Configure report
config = ReportConfig(
    start_date="2024-01-01",
    end_date="2024-02-01",
    linked_account_ids=["123456789012"],
    granularity=Granularity.MONTHLY,
    group_by=[GroupBy.USAGE_TYPE],
    filters={FilterDimension.SERVICE: ["Amazon Relational Database Service"]},
    tag_filters={"customer": ["CustomerName"]}
)

# Generate and export
data = reporter.generate_report(config)
reporter.export_to_csv(data, "report.csv")
```

## Extending the Framework

### Adding New Report Types

Create a new function in `examples.py`:

```python
def my_custom_report():
    reporter = AWSCostReporter()
    
    config = ReportConfig(
        start_date="2024-01-01", 
        end_date="2024-02-01",
        # Your custom configuration
    )
    
    data = reporter.generate_report(config)
    reporter.export_to_csv(data, "my_report.csv")
```

### Available Options

**Services**: Add to service_map in `cost_cli.py` or use full AWS service names

**Group By Options**:
- `service`, `usage_type`, `instance_type`, `region`
- `availability_zone`, `operation`, `purchase_type`, `platform`, `tenancy`

**Filter Dimensions**:
- `service`, `linked_account`, `region`, `usage_type`
- `instance_type`, `operation`
- Any tag key for tag filtering

### Future Extensions

The framework supports:

1. **New Services**: Just add service names to filters
2. **New Metrics**: Modify `metrics` in ReportConfig
3. **New Groupings**: AWS Cost Explorer supports many dimensions
4. **New Output Formats**: Extend export methods
5. **Scheduled Reports**: Add cron/scheduling wrapper
6. **Email/Slack Integration**: Add notification methods
7. **Cost Budgets/Alerts**: Integrate with AWS Budgets API

## Files

- `aws_cost_tools/`: Package
  - `reporter.py`: Main framework classes
  - `cli.py`: Command-line interface (exposed as `cost-tools`)
  - `examples.py`: Programmatic examples (exposed as `cost-tools-examples`)
- `aws_cost_reporter.py`: Legacy module (kept for compatibility)
- `cost_cli.py`: Legacy CLI script (kept for compatibility)
- `examples.py`: Legacy examples (kept for compatibility)
- `pyproject.toml`: Project metadata and dependencies (uv-compatible)
- `uv.lock`: Resolved dependency lockfile
- `README.md`: This documentation

## AWS Permissions Required

Your AWS credentials need `ce:GetCostAndUsage` and `ce:GetDimensionValues` permissions.

## Notes

- Cost Explorer API requires `us-east-1` region
- Data is typically available with 24-48 hour delay
- Large date ranges may take time to process
- CSV files include all requested metrics (BlendedCost, UnblendedCost)