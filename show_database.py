#!/usr/bin/env python3
"""
Script to visualize the database structure and current data
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from sqlalchemy import text
from datetime import datetime

def show_database_structure():
    print("=" * 80)
    print("📊 TASK TRACKER DATABASE STRUCTURE")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Show table structure
        print("\n🗂️  DATABASE SCHEMA:")
        print("-" * 50)
        
        # Show Users table structure
        print("\n👥 USERS Table:")
        print("   • id (Primary Key, Auto-increment)")
        print("   • email (Unique, Indexed)")
        print("   • hashed_password (String 255)")
        print("   • role (Enum: 'user' | 'admin')")
        print("   • created_at (Timestamp)")
        print("   • Relationship: One-to-Many with Tasks")
        
        # Show Tasks table structure  
        print("\n📋 TASKS Table:")
        print("   • id (Primary Key, Auto-increment)")
        print("   • owner_id (Foreign Key → users.id, Cascade Delete)")
        print("   • title (String 255, Required)")
        print("   • description (Text, Optional)")
        print("   • due_date (Date, Optional)")
        print("   • status (Enum: 'pending' | 'in_progress' | 'done')")
        print("   • created_at (Timestamp)")
        print("   • updated_at (Timestamp, Auto-update)")
        print("   • Relationship: Many-to-One with User")
        
        # Show current data
        print("\n" + "=" * 80)
        print("📈 CURRENT DATABASE CONTENT")
        print("=" * 80)
        
        # Users data
        users = db.query(User).all()
        print(f"\n👥 USERS ({len(users)} total):")
        print("-" * 50)
        for user in users:
            task_count = db.query(Task).filter(Task.owner_id == user.id).count()
            print(f"   🆔 ID: {user.id}")
            print(f"   ✉️  Email: {user.email}")
            print(f"   🛡️  Role: {user.role.value}")
            print(f"   📅 Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📝 Tasks: {task_count}")
            print()
        
        # Tasks data
        tasks = db.query(Task).all()
        print(f"\n📋 TASKS ({len(tasks)} total):")
        print("-" * 50)
        for task in tasks:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            print(f"   🆔 ID: {task.id}")
            print(f"   📝 Title: {task.title}")
            print(f"   📄 Description: {task.description or 'N/A'}")
            print(f"   👤 Owner: {owner.email if owner else 'Unknown'}")
            print(f"   📊 Status: {task.status.value}")
            print(f"   📅 Due Date: {task.due_date or 'N/A'}")
            print(f"   🕐 Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🔄 Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Summary statistics
        print("=" * 80)
        print("📊 DATABASE STATISTICS")
        print("=" * 80)
        
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.role == UserRole.admin).count()
        regular_users = db.query(User).filter(User.role == UserRole.user).count()
        
        total_tasks = db.query(Task).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.pending).count()
        in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.in_progress).count()
        done_tasks = db.query(Task).filter(Task.status == TaskStatus.done).count()
        
        print(f"\n👥 User Statistics:")
        print(f"   Total Users: {total_users}")
        print(f"   Admin Users: {admin_users}")
        print(f"   Regular Users: {regular_users}")
        
        print(f"\n📋 Task Statistics:")
        print(f"   Total Tasks: {total_tasks}")
        print(f"   Pending: {pending_tasks}")
        print(f"   In Progress: {in_progress_tasks}")
        print(f"   Done: {done_tasks}")
        
        # Relationships demonstration
        print(f"\n🔗 Relationship Examples:")
        if users and tasks:
            sample_user = users[0]
            user_tasks = db.query(Task).filter(Task.owner_id == sample_user.id).all()
            print(f"   User '{sample_user.email}' owns {len(user_tasks)} tasks:")
            for task in user_tasks[:3]:  # Show first 3
                print(f"     • {task.title}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    show_database_structure()
