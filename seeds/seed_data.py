from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.core.security import get_password_hash
from datetime import date, timedelta
import argparse

"""Seed script to insert initial users and tasks.
Safe to run multiple times: it checks for existing seed users by email.
Now also supports adding N tasks for a specific user via CLI args.

Usage examples inside container:
  # Seed base users + 3 tasks each
  python seeds/seed_data.py --base

  # Add (or ensure) 15 tasks exist for a user
  python seeds/seed_data.py --user-email ali@emumba.com --tasks 15

If both --base and --user-email/--tasks are provided, base seeding runs first.
"""

def seed_base():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email=='alice@example.com').first():
            print("Seed users already exist; skipping base seeding.")
            return
        u1 = User(email='alice@example.com', hashed_password=get_password_hash('Password1!'), role=UserRole.admin)
        u2 = User(email='bob@example.com',   hashed_password=get_password_hash('Password1!'), role=UserRole.user)
        u3 = User(email='carol@example.com', hashed_password=get_password_hash('Password1!'), role=UserRole.user)
        db.add_all([u1,u2,u3])
        db.flush()
        for u in (u1,u2,u3):
            base = u.email.split('@')[0]
            for i in range(1,4):
                task = Task(
                    owner_id=u.id,
                    title=f"Task {i} for {base}",
                    description=f"Auto-generated task {i} for {u.email}",
                    due_date=date.today() + timedelta(days=i),
                    status=TaskStatus.pending if i < 3 else TaskStatus.in_progress
                )
                db.add(task)
        db.commit()
        print("Base seed data inserted.")
    finally:
        db.close()


def seed_tasks_for_user(email: str, total_tasks: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found. Create the user first (e.g., via /auth/register).")
            return
        existing = db.query(Task).filter(Task.owner_id == user.id).count()
        if existing >= total_tasks:
            print(f"User {email} already has {existing} tasks (>= requested {total_tasks}); nothing to do.")
            return
        to_create = total_tasks - existing
        print(f"Creating {to_create} tasks for {email} (will reach {total_tasks}).")
        for i in range(existing + 1, total_tasks + 1):
            t = Task(
                owner_id=user.id,
                title=f"{user.email.split('@')[0].capitalize()} Task {i}",
                description=f"Auto-generated task {i} for {email}",
                due_date=date.today() + timedelta(days=i),
                status=TaskStatus.pending if i % 3 else TaskStatus.in_progress
            )
            db.add(t)
        db.commit()
        print(f"Done. User {email} now has {db.query(Task).filter(Task.owner_id==user.id).count()} tasks.")
    finally:
        db.close()


def run():  # backward compatibility
    seed_base()


def main():
    parser = argparse.ArgumentParser(description="Seeder CLI")
    parser.add_argument('--base', action='store_true', help='Run base seeding (3 users + 3 tasks each)')
    parser.add_argument('--user-email', type=str, help='User email to seed tasks for')
    parser.add_argument('--tasks', type=int, help='Ensure this total number of tasks for the user')
    args = parser.parse_args()

    if not any([args.base, args.user_email]):
        parser.print_help()
        return

    if args.base:
        seed_base()

    if args.user_email and args.tasks:
        seed_tasks_for_user(args.user_email, args.tasks)
    elif args.user_email and not args.tasks:
        print('--tasks required when --user-email is provided')


if __name__ == "__main__":
    main()
