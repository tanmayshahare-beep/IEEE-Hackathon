"""
Initialize MongoDB Database for AgroDoc-AI

This script:
1. Connects to MongoDB
2. Creates test user if not exists
3. Verifies database connection
"""

from pymongo import MongoClient
from datetime import datetime
import bcrypt

# MongoDB connection
MONGODB_URI = "mongodb://localhost:27017/agrodoc-ai"

print("=" * 60)
print("  MongoDB Initialization Script")
print("=" * 60)
print()

try:
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.server_info()
    print("✓ Connected to MongoDB successfully!")
    print()
    
    # Get database
    db = client['agrodoc-ai']
    
    # List collections
    collections = db.list_collection_names()
    print(f"Collections: {collections}")
    print()
    
    # Check if users collection exists
    if 'users' not in collections:
        print("Creating users collection...")
        db.create_collection('users')
        print("✓ Users collection created!")
        print()
    
    # Check if test user exists
    test_user = db.users.find_one({'username': 'testuser'})
    
    if test_user:
        print("✓ Test user already exists:")
        print(f"  Username: {test_user['username']}")
        print(f"  Email: {test_user['email']}")
        print(f"  User ID: {test_user['_id']}")
    else:
        print("Creating test user...")
        
        # Hash password
        password = 'test123'
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create test user
        test_user_doc = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': hashed_password,
            'email_verified': True,
            'location': {
                'type': 'manual',
                'manual': {
                    'state': 'Maharashtra',
                    'district': 'Mumbai'
                }
            },
            'farm_boundaries': None,
            'predictions': [],
            'created_at': datetime.utcnow()
        }
        
        result = db.users.insert_one(test_user_doc)
        print(f"✓ Test user created with ID: {result.inserted_id}")
        print()
        print("Test credentials:")
        print("  Username: testuser")
        print("  Password: test123")
    
    print()
    print("=" * 60)
    print("  Database initialization complete!")
    print("=" * 60)
    print()
    print("You can now login with:")
    print("  Username: testuser")
    print("  Password: test123")
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Troubleshooting steps:")
    print("1. Make sure MongoDB is running")
    print("2. Check MongoDB connection string in .env")
    print("3. Try restarting MongoDB service")
    print()
    
    # Show MongoDB status
    import subprocess
    try:
        result = subprocess.run(['tasklist', '|', 'findstr', 'mongo'], 
                              capture_output=True, text=True, shell=True)
        if result.stdout:
            print("MongoDB process found:")
            print(result.stdout)
        else:
            print("⚠️  MongoDB is NOT running!")
            print()
            print("To start MongoDB, run:")
            print("  net start MongoDB")
            print("  OR")
            print("  mongod --dbpath C:\\data\\db")
    except:
        pass
