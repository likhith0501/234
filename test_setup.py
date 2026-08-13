#!/usr/bin/env python
"""Test script to verify HepatoX application setup."""

import sys

def main():
    try:
        print("Testing HepatoX Application Setup...")
        print("-" * 50)
        
        print("1. Importing Flask app...", end=" ")
        from app import app, db
        print("✓")
        
        print("2. Initializing app context...", end=" ")
        with app.app_context():
            print("✓")
            
            print("3. Creating database tables...", end=" ")
            db.create_all()
            print("✓")
            
            print("4. Checking database connection...", end=" ")
            from database import User
            user_count = User.query.count()
            print(f"✓ ({user_count} users)")
            
        print("-" * 50)
        print("✓ All tests passed! Application is ready.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

