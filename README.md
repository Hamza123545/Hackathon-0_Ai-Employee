# AI Employee - Platinum Tier 🏆

**The Autonomous Digital FTE (Full-Time Equivalent)**

Welcome to the **Platinum Tier** AI Employee. This is not just a chatbot; it's a fully autonomous, hybrid-cloud agent capable of running your business 24/7. It combines a robust Python backend with a premium Next.js Frontend Command Center.

## 🌟 Key Features

### 1. 🧠 Zone Awareness ("Split Brain" Architecture)
The agent operates in two distinct modes to balance automation with security:
*   **☁️ Cloud Agent**: Runs 24/7 (e.g., in Docker).
    *   *Duties*: Monitors Emails, WhatsApp, LinkedIn; Drafts replies; Audits finances.
    *   *Security*: **Read-Only** on banking/sensitive credentials. Cannot send money or messages without approval.
*   **💻 Local Agent**: Runs on your secure machine.
    *   *Duties*: **Executes** approved actions. Signs checks, sends WhatsApp messages via your local session.

### 2. 🎛️ Premium Command Center (Frontend)
A "Proper" Dashboard built with **Next.js**, **Framer Motion**, and **Shadcn UI**.
*   **Service Manager**: Complete control over your agent's senses.
    *   **Toggle Watchers**: Turn specific modules (Gmail, WhatsApp, LinkedIn) **ON** or **OFF** individually.
    *   *Example*: "I want Gmail monitoring ON, but WhatsApp OFF for the weekend." -> Just click the toggle.
*   **Live Status**: Real-time heartbeat monitoring of all backend processes.
*   **Theming**: Beautiful Light/Dark mode support.
*   **Animations**: Smooth, professional transitions and hover effects.

### 3. 🏢 Enterprise Integration (Gold Tier)
*   **Odoo ERP**: Fully integrated with Odoo for accounting and inventory management.
*   **Weekly Audits**: The agent wakes up every Monday to audit your finances and generate a "CEO Briefing."

---

## 🚀 Installation & Setup

### Prerequisites
*   Node.js v18+
*   Python 3.10+
*   Docker (Optional, for Cloud mode)
*   PM2 (`npm install -g pm2`)

### Option A: Local Power User (Windows/Mac)
Run everything on your machine for full control.

1.  **Setup Configuration**:
    Copy `.env.example` to `.env` and fill in your keys.

2.  **Start the Backend (PM2)**:
    ```powershell
    # Windows PowerShell
    cd AI_Employee
    $env:AGENT_MODE="local"
    $env:HEADLESS="false" 
    pm2 start ecosystem.config.js
    ```
    *   *Note*: `HEADLESS="false"` allows the WhatsApp browser to open so you can scan the QR code.

3.  **Start the Frontend**:
    ```bash
    cd AI_Employee/web-ui
    npm install
    npm run dev
    ```
    Access the Dashboard at: `http://localhost:3000`

### Option B: Cloud Deployment (Docker)
Deploy the "Brain" to the cloud for 24/7 monitoring.

1.  **Build & Run**:
    ```bash
    docker-compose up --build -d
    ```
    The container automatically runs in **Cloud Mode** (Headless), ensuring it safely monitors without trying to open visible windows.

---

## 🎮 How to Use the Service Manager

Navigate to the **Services** page in the Dashboard. You will see a card for each agent component:

| Service | Description | Control |
| :--- | :--- | :--- |
| **Autonomous Agent** | The main brain (Ralph Wiggum Loop). | **Start/Stop** |
| **Gmail Watcher** | Monitors Inbox for urgent emails. | **Toggle ON/OFF** |
| **WhatsApp Watcher** | Monitors chat for "Urgent", "Payment". | **Toggle ON/OFF** |
| **LinkedIn Watcher** | Checks for new leads/messages. | **Toggle ON/OFF** |
| **Orchestrator** | Manages the Approval Workflow. | **Auto-Runs** |

*Tip: If you are going on vacation, you can stop the `Autonomous Agent` but leave the `Watchers` running to collect data!*

---

## 📂 Project Structure

```
AI_Employee/
├── autonomous_agent.py   # The Brain (Zone Aware)
├── ecosystem.config.js   # PM2 Process Manager
├── watchers/            # Sensory Inputs (Gmail, WhatsApp, etc.)
├── mcp_servers/         # Tools (Odoo, Email, Browser)
├── web-ui/              # Next.js Frontend
│   ├── app/             # Dashboard Pages
│   └── components/      # UI Components (ServiceManager, etc.)
└── Dockerfile           # Cloud Deployment Config
```

---

**Platinum Tier Status**: ✅ 100% Complete
*Hackathon 0 Submission*
