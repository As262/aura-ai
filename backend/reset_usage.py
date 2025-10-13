#!/usr/bin/env python
"""
Simple script to reset usage count for testing purposes.
This will reset your IP's usage count to 0 so you can test the application again.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_ai.settings')
django.setup()

from api.models import IPUsage


def reset_all_usage():
    """Reset usage count for all IP addresses"""
    try:
        count = IPUsage.objects.all().count()
        IPUsage.objects.all().delete()
        print(f"✅ Reset usage for {count} IP addresses")
        return True
    except Exception as e:
        print(f"❌ Error resetting usage: {e}")
        return False


def reset_usage_for_ip(ip_address):
    """Reset usage count for a specific IP address"""
    try:
        obj = IPUsage.objects.filter(ip_address=ip_address).first()
        if obj:
            obj.count = 0
            obj.save()
            print(f"✅ Reset usage count to 0 for IP: {ip_address}")
        else:
            print(f"ℹ️  No usage record found for IP: {ip_address}")
        return True
    except Exception as e:
        print(f"❌ Error resetting usage for IP {ip_address}: {e}")
        return False


def list_all_usage():
    """List all IP addresses and their current usage counts"""
    try:
        usage_records = IPUsage.objects.all().order_by('-count')
        if not usage_records:
            print("ℹ️  No usage records found")
            return
        
        print("\n📊 Current Usage Statistics:")
        print("-" * 50)
        for record in usage_records:
            print(f"IP: {record.ip_address:<15} | Usage: {record.count:<3} | Updated: {record.last_updated}")
        print("-" * 50)
        print(f"Total IPs tracked: {usage_records.count()}")
    except Exception as e:
        print(f"❌ Error listing usage: {e}")


if __name__ == "__main__":
    print("🔧 Aura AI Usage Reset Tool")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python reset_usage.py all              - Reset all IP usage")
        print("  python reset_usage.py list             - List all IP usage")
        print("  python reset_usage.py reset <IP>       - Reset specific IP")
        print("  python reset_usage.py reset localhost  - Reset localhost (127.0.0.1)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "all":
        reset_all_usage()
    
    elif command == "list":
        list_all_usage()
    
    elif command == "reset":
        if len(sys.argv) < 3:
            print("❌ Please specify an IP address to reset")
            print("Example: python reset_usage.py reset 127.0.0.1")
            sys.exit(1)
        
        ip = sys.argv[2]
        if ip.lower() == "localhost":
            ip = "127.0.0.1"
        
        reset_usage_for_ip(ip)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: all, list, reset")
        sys.exit(1)
    
    print("\n✨ Done!")