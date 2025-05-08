#!/usr/bin/env python3
"""
AWS Resource Enrichment for Terraform Visualization
Adds additional metadata from AWS API to enhance visualizations
"""

import os
import sys
import json
import argparse
import boto3
from botocore.exceptions import ClientError

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enrich Terraform visualizations with AWS API data')
    parser.add_argument('--visualization-dir', required=True, help='Directory containing visualization files')
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    parser.add_argument('--profile', help='AWS profile to use')
    return parser.parse_args()

def get_aws_session(profile=None, region=None):
    """Create an AWS session"""
    session_args = {}
    if profile:
        session_args['profile_name'] = profile
    if region:
        session_args['region_name'] = region
    
    return boto3.Session(**session_args)

def enrich_s3_buckets(session, resources):
    """Add S3 bucket metadata"""
    s3_client = session.client('s3')
    enriched_data = {}
    
    for resource_name, resource_id in resources.get('aws_s3_bucket', {}).items():
        try:
            bucket_name = resource_id.split('/')[-1]
            response = s3_client.get_bucket_location(Bucket=bucket_name)
            
            enriched_data[resource_name] = {
                'name': bucket_name,
                'region': response.get('LocationConstraint', 'us-east-1'),
                'resource_id': resource_id
            }
            
            # Try to get bucket size
            try:
                metrics = s3_client.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='BucketSizeBytes',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': bucket_name},
                        {'Name': 'StorageType', 'Value': 'StandardStorage'}
                    ],
                    StartTime=datetime.datetime.now() - datetime.timedelta(days=2),
                    EndTime=datetime.datetime.now(),
                    Period=86400,
                    Statistics=['Average']
                )
                if metrics['Datapoints']:
                    enriched_data[resource_name]['size_bytes'] = metrics['Datapoints'][0]['Average']
            except Exception as e:
                # Metrics might not be available, that's ok
                pass
                
        except ClientError as e:
            print(f"Error getting data for bucket {bucket_name}: {e}")
    
    return enriched_data

def enrich_ec2_instances(session, resources):
    """Add EC2 instance metadata"""
    ec2_client = session.client('ec2')
    enriched_data = {}
    
    instance_ids = []
    resource_map = {}
    
    # Extract instance IDs from resource IDs
    for resource_name, resource_id in resources.get('aws_instance', {}).items():
        instance_id = resource_id.split('/')[-1]
        instance_ids.append(instance_id)
        resource_map[instance_id] = resource_name
    
    if not instance_ids:
        return enriched_data
    
    # Get instance data in batches
    try:
        response = ec2_client.describe_instances(InstanceIds=instance_ids)
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance['InstanceId']
                resource_name = resource_map.get(instance_id)
                
                if resource_name:
                    enriched_data[resource_name] = {
                        'instance_id': instance_id,
                        'state': instance.get('State', {}).get('Name'),
                        'instance_type': instance.get('InstanceType'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'launch_time': instance.get('LaunchTime').isoformat() if 'LaunchTime' in instance else None,
                    }
    except ClientError as e:
        print(f"Error getting EC2 instance data: {e}")
    
    return enriched_data

def enrich_resources(session, resources):
    """Enrich resources with AWS API data"""
    enriched = {}
    
    # Add S3 bucket data
    if 'aws_s3_bucket' in resources:
        enriched['s3_buckets'] = enrich_s3_buckets(session, resources)
    
    # Add EC2 instance data
    if 'aws_instance' in resources:
        enriched['ec2_instances'] = enrich_ec2_instances(session, resources)
    
    # Add more resource types as needed
    
    return enriched

def extract_resources_from_visualization(visualization_dir):
    """Extract resource IDs from visualization data"""
    resources_file = os.path.join(visualization_dir, 'resources.json')
    
    if not os.path.exists(resources_file):
        print(f"Error: Resources file not found at {resources_file}")
        return None
    
    with open(resources_file, 'r') as f:
        return json.load(f)

def save_enriched_data(visualization_dir, enriched_data):
    """Save enriched data to visualization directory"""
    output_file = os.path.join(visualization_dir, 'enriched_resources.json')
    
    with open(output_file, 'w') as f:
        json.dump(enriched_data, f, indent=2)
    
    print(f"Enriched data saved to {output_file}")

def main():
    args = parse_args()
    
    # Check if visualization directory exists
    if not os.path.isdir(args.visualization_dir):
        print(f"Error: Visualization directory {args.visualization_dir} not found")
        return 1
    
    # Extract resources from visualization
    resources = extract_resources_from_visualization(args.visualization_dir)
    if not resources:
        return 1
    
    # Create AWS session
    try:
        session = get_aws_session(args.profile, args.region)
        
        # Check if we can access AWS
        account_id = session.client('sts').get_caller_identity().get('Account')
        print(f"Connected to AWS account {account_id}")
    except Exception as e:
        print(f"Error connecting to AWS: {e}")
        print("Proceeding without enrichment")
        return 1
    
    # Enrich resources with AWS API data
    enriched_data = enrich_resources(session, resources)
    
    # Save enriched data
    save_enriched_data(args.visualization_dir, enriched_data)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 