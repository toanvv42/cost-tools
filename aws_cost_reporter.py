#!/usr/bin/env python3

import boto3
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import argparse
import sys

class Granularity(Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    HOURLY = "HOURLY"

class GroupBy(Enum):
    SERVICE = "SERVICE"
    USAGE_TYPE = "USAGE_TYPE"
    INSTANCE_TYPE = "INSTANCE_TYPE"
    REGION = "REGION"
    AVAILABILITY_ZONE = "AVAILABILITY_ZONE"
    OPERATION = "OPERATION"
    PURCHASE_TYPE = "PURCHASE_TYPE"
    PLATFORM = "PLATFORM"
    TENANCY = "TENANCY"

class FilterDimension(Enum):
    SERVICE = "SERVICE"
    LINKED_ACCOUNT = "LINKED_ACCOUNT"
    REGION = "REGION"
    USAGE_TYPE = "USAGE_TYPE"
    INSTANCE_TYPE = "INSTANCE_TYPE"
    OPERATION = "OPERATION"

@dataclass
class ReportConfig:
    """Configuration for cost reports"""
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    linked_account_ids: Optional[List[str]] = None
    granularity: Granularity = Granularity.MONTHLY
    group_by: Optional[List[GroupBy]] = None
    filters: Optional[Dict[Union[FilterDimension, str], List[str]]] = None  # str for TAG keys
    tag_filters: Optional[Dict[str, List[str]]] = None  # Separate for clarity
    metrics: List[str] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = ['BlendedCost', 'UnblendedCost']
        if self.group_by is None:
            self.group_by = []

class AWSCostReporter:
    """Main class for generating AWS cost reports"""
    
    def __init__(self, profile_name: Optional[str] = None, region: str = 'us-east-1'):
        """
        Initialize the cost reporter
        
        Args:
            profile_name: AWS profile name (optional)
            region: AWS region for Cost Explorer API (us-east-1 is required)
        """
        session = boto3.Session(profile_name=profile_name)
        self.ce_client = session.client('ce', region_name=region)
        
    def generate_report(self, config: ReportConfig) -> Dict[str, Any]:
        """
        Generate cost report based on configuration
        
        Args:
            config: ReportConfig object with all parameters
            
        Returns:
            Raw AWS Cost Explorer API response
        """
        # Build group by clause
        group_by_clause = []
        for group in config.group_by:
            group_by_clause.append({'Type': 'DIMENSION', 'Key': group.value})
        
        # Add tag grouping if specified
        if config.tag_filters:
            for tag_key in config.tag_filters.keys():
                group_by_clause.append({'Type': 'TAG', 'Key': tag_key})
        
        # Build filter clause
        filter_clause = self._build_filter_clause(config)
        
        # Make API call
        params = {
            'TimePeriod': {
                'Start': config.start_date,
                'End': config.end_date
            },
            'Granularity': config.granularity.value,
            'Metrics': config.metrics
        }
        
        if group_by_clause:
            params['GroupBy'] = group_by_clause
            
        if filter_clause:
            params['Filter'] = filter_clause
            
        response = self.ce_client.get_cost_and_usage(**params)
        return response
    
    def _build_filter_clause(self, config: ReportConfig) -> Optional[Dict[str, Any]]:
        """Build the filter clause for Cost Explorer API"""
        filters = []
        
        # Linked account filter
        if config.linked_account_ids:
            filters.append({
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': config.linked_account_ids
                }
            })
        
        # Dimension filters
        if config.filters:
            for filter_key, filter_values in config.filters.items():
                if isinstance(filter_key, FilterDimension):
                    filters.append({
                        'Dimensions': {
                            'Key': filter_key.value,
                            'Values': filter_values
                        }
                    })
        
        # Tag filters
        if config.tag_filters:
            for tag_key, tag_values in config.tag_filters.items():
                filters.append({
                    'Tags': {
                        'Key': tag_key,
                        'Values': tag_values
                    }
                })
        
        # Return appropriate filter structure
        if len(filters) == 0:
            return None
        elif len(filters) == 1:
            return filters[0]
        else:
            return {'And': filters}
    
    def export_to_csv(self, report_data: Dict[str, Any], output_file: str, 
                      flatten_groups: bool = True) -> None:
        """
        Export report data to CSV
        
        Args:
            report_data: Raw API response from generate_report()
            output_file: Output CSV file path
            flatten_groups: Whether to flatten group keys into separate columns
        """
        if not report_data.get('ResultsByTime'):
            print("No data to export")
            return
            
        rows = []
        
        for time_result in report_data['ResultsByTime']:
            time_period = time_result['TimePeriod']
            start_date = time_period['Start']
            end_date = time_period['End']
            
            if not time_result.get('Groups'):
                # No grouping - just overall totals
                for metric_name, metric_data in time_result.get('Total', {}).items():
                    rows.append({
                        'StartDate': start_date,
                        'EndDate': end_date,
                        'Metric': metric_name,
                        'Amount': float(metric_data.get('Amount', 0)),
                        'Unit': metric_data.get('Unit', 'USD')
                    })
            else:
                # With grouping
                for group in time_result['Groups']:
                    base_row = {
                        'StartDate': start_date,
                        'EndDate': end_date
                    }
                    
                    # Handle group keys
                    if flatten_groups and group.get('Keys'):
                        for i, key in enumerate(group['Keys']):
                            base_row[f'GroupBy_{i+1}'] = key
                    else:
                        base_row['GroupKeys'] = '|'.join(group.get('Keys', []))
                    
                    # Add metrics
                    for metric_name, metric_data in group.get('Metrics', {}).items():
                        row = base_row.copy()
                        row.update({
                            'Metric': metric_name,
                            'Amount': float(metric_data.get('Amount', 0)),
                            'Unit': metric_data.get('Unit', 'USD')
                        })
                        rows.append(row)
        
        # Write to CSV
        if rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"Report exported to: {output_file}")
        else:
            print("No data to export")
    
    def get_linked_accounts(self) -> Dict[str, str]:
        """Get all linked account IDs and names"""
        response = self.ce_client.get_dimension_values(
            Dimension='LINKED_ACCOUNT',
            Context='COST_AND_USAGE'
        )
        return {
            item['Value']: item.get('Attributes', {}).get('description', 'Unknown')
            for item in response['DimensionValues']
        }
    
    def get_tag_values(self, tag_key: str) -> List[str]:
        """Get all possible values for a specific tag"""
        response = self.ce_client.get_dimension_values(
            Dimension='TAG',
            Context='COST_AND_USAGE',
            SearchString=tag_key
        )
        return [item['Value'] for item in response['DimensionValues']]
    
    def get_services(self) -> List[str]:
        """Get all available services"""
        response = self.ce_client.get_dimension_values(
            Dimension='SERVICE',
            Context='COST_AND_USAGE'
        )
        return [item['Value'] for item in response['DimensionValues']]

def create_sample_configs():
    """Create some sample report configurations"""
    
    # RDS costs by usage type for specific customer
    rds_by_usage = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01",
        linked_account_ids=["123456789012"],
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.USAGE_TYPE],
        filters={FilterDimension.SERVICE: ["Amazon Relational Database Service"]},
        tag_filters={"customer": ["CustomerName"]}
    )
    
    # Daily EC2 costs by instance type
    ec2_daily = ReportConfig(
        start_date="2024-01-01", 
        end_date="2024-01-08",
        granularity=Granularity.DAILY,
        group_by=[GroupBy.INSTANCE_TYPE],
        filters={FilterDimension.SERVICE: ["Amazon Elastic Compute Cloud - Compute"]}
    )
    
    # All services for multiple accounts
    all_services = ReportConfig(
        start_date="2024-01-01",
        end_date="2024-02-01", 
        linked_account_ids=["123456789012", "987654321098"],
        granularity=Granularity.MONTHLY,
        group_by=[GroupBy.SERVICE]
    )
    
    return {
        'rds_by_usage': rds_by_usage,
        'ec2_daily': ec2_daily,
        'all_services': all_services
    }

def main():
    # Delegate to the packaged CLI to avoid duplication
    from aws_cost_tools.cli import main as pkg_main
    return pkg_main()

if __name__ == "__main__":
    main()