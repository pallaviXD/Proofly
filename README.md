# 📚 Proofly - Proof-of-Learning Tracker

A minimal full-stack web application to track and showcase your learning journey.

## Features

- ✅ **User Authentication** - Secure signup and login
- ✅ **Skill Management** - Add and track multiple skills
- ✅ **Learning Entries** - Log daily learning with date, time spent, topics, and takeaways
- ✅ **Public Proof Pages** - Share read-only proof of your learning journey
- ✅ **Progress Tracking** - See total time invested per skill

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Styling | Tailwind CSS |

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills table
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    public_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Learning entries table
CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL,
    date DATE NOT NULL,
    time_spent INTEGER NOT NULL,
    what_studied TEXT NOT NULL,
    key_takeaway TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/signup` | Register new user |
| POST | `/api/login` | Login user |
| POST | `/api/logout` | Logout user |
| GET | `/api/me` | Get current user |

### Skills
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills` | Get all user's skills |
| POST | `/api/skills` | Create new skill |
| DELETE | `/api/skills/:id` | Delete a skill |

### Entries
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills/:id/entries` | Get entries for skill |
| POST | `/api/skills/:id/entries` | Add new entry |
| DELETE | `/api/entries/:id` | Delete an entry |

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/proof/:public_id` | Get public proof page |

## Setup & Installation

### 1. Clone or download the project

```bash
cd proofly
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

### 5. Open in browser

Navigate to `http://localhost:5000`

## How to Use

1. **Sign Up** - Create an account with username, email, and password
2. **Login** - Access your dashboard
3. **Add Skill** - Click "Add Skill" and enter a skill name (e.g., Python, Web Development)
4. **Log Entry** - Select a skill and log your daily learning:
   - Date of learning
   - Time spent (in minutes)
   - What you studied
   - Key takeaway (1-2 sentences)
5. **Share Proof** - Click the share icon to get a public link to your proof page

## Project Structure

```
proofly/
├── app.py              # Flask backend
├── index.html          # Frontend (single page app)
├── requirements.txt    # Python dependencies
├── README.md           # Documentation
└── proofly.db          # SQLite database (auto-created)
```

## Demo Mode

The frontend works in demo mode (localStorage) when the backend is not running. Connect to Flask for full functionality.

---

Made with ❤️ for lifelong learners