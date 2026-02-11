# How to Use This Repository 📖

Welcome to the **Platinum Tier AI Employee** repository. This guide explains how to navigate the project documentation and get started.

## 📂 Primary Documentation
The main source of truth is the **[README.md](./README.md)** file located at the root of this directory.

**The README.md covers:**
1.  **Architecture**: Explains the "Split-Brain" (Cloud vs. Local) design.
2.  **Features**: Details the Dashboard, Dark Mode, and Service Manager.
3.  **Installation**: Step-by-step commands for:
    *   **Cloud Deployment** (Docker)
    *   **Local Development** (PM2 + Node.js)
4.  **Usage**: How to use the "Service Manager" to toggle specific watchers (e.g., enable Gmail but disable WhatsApp).

## 🚀 Quick Start Summary
*If you are in a rush, follow these steps (detailed in README.md):*

1.  **Read [README.md](./README.md)** for your specific OS requirements.
2.  **Configure Environment**: Copy `.env.example` to `.env` inside `AI_Employee/`.
3.  **Launch Backend**:
    *   *Cloud*: `docker-compose up -d`
    *   *Local*: `pm2 start ecosystem.config.js`
4.  **Launch Frontend**:
    *   `cd AI_Employee/web-ui` -> `npm install` -> `npm run dev`
5.  **Access Dashboard**: Open `http://localhost:3000`

## 🧩 Repo Structure
*   **`AI_Employee/`**: Backend Python code (The Brain).
*   **`AI_Employee/web-ui/`**: Frontend Next.js code (The Command Center).
*   **`docker-compose.yml`**: Configuration for running the agent in a container.

---
*Refer to [README.md](./README.md) for full details.*
