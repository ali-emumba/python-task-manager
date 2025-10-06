## 🗄️ Task Tracker Database Structure

### 📊 Entity Relationship Diagram

```
┌─────────────────────────────────────┐         ┌─────────────────────────────────────┐
│                USERS                │         │                TASKS                │
├─────────────────────────────────────┤         ├─────────────────────────────────────┤
│ 🔑 id (PK)            INTEGER       │ 1    ∞  │ 🔑 id (PK)            INTEGER       │
│ 📧 email              VARCHAR(255)  │ ←──────→ │ 👤 owner_id (FK)      INTEGER       │
│ 🔒 hashed_password    VARCHAR(255)  │         │ 📝 title              VARCHAR(255)  │
│ 🛡️  role               ENUM          │         │ 📄 description        TEXT          │
│ 📅 created_at         TIMESTAMP     │         │ 📅 due_date           DATE          │
└─────────────────────────────────────┘         │ 📊 status             ENUM          │
                                                │ 🕐 created_at         TIMESTAMP     │
                                                │ 🔄 updated_at         TIMESTAMP     │
                                                └─────────────────────────────────────┘
```

### 🔍 Database Constraints & Indexes

```sql
-- USERS table constraints
CONSTRAINT users_pkey PRIMARY KEY (id)
CONSTRAINT users_email_key UNIQUE (email)
INDEX ix_users_id ON users(id)
INDEX ix_users_email ON users(email)

-- TASKS table constraints
CONSTRAINT tasks_pkey PRIMARY KEY (id)
CONSTRAINT tasks_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
INDEX ix_tasks_id ON tasks(id)
INDEX ix_tasks_owner_id ON tasks(owner_id)
```

### 🎯 Enum Types

```sql
-- User roles
CREATE TYPE userrole AS ENUM ('user', 'admin');

-- Task statuses
CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'done');
```

### 🔗 Relationships

- **One-to-Many**: User → Tasks
  - One user can have multiple tasks
  - Each task belongs to exactly one user
  - Cascade delete: When user is deleted, all their tasks are deleted

### 📊 Current Data Distribution

```
Users (6 total):
├── 👑 Admin (1): alice@example.com
└── 👤 Regular Users (5):
    ├── aliii@emumba.com (0 tasks)
    ├── user@example.com (0 tasks)
    ├── ali@email.com (0 tasks)
    ├── bob@example.com (3 tasks)
    └── carol@example.com (3 tasks)

Tasks (9 total):
├── 📋 Pending (6 tasks)
├── 🔄 In Progress (3 tasks)
└── ✅ Done (0 tasks)
```

### 🚀 Sample Queries Your App Uses

```sql
-- Get all tasks for a user (ownership protection)
SELECT * FROM tasks WHERE owner_id = $1;

-- Admin view all tasks
SELECT t.*, u.email as owner_email
FROM tasks t
JOIN users u ON t.owner_id = u.id;

-- Search tasks by title
SELECT * FROM tasks
WHERE owner_id = $1 AND title ILIKE '%search%';

-- Filter by status and date
SELECT * FROM tasks
WHERE owner_id = $1
  AND status = 'pending'
  AND due_date BETWEEN $2 AND $3;
```

### 🔧 Migration History

```
migrations/versions/
└── 6196e34e17ee_init.py  # Initial schema creation
    ├── Created users table
    ├── Created tasks table
    ├── Set up foreign key relationship
    └── Added indexes for performance
```
