![bytebrew_logo](assets/bytebrew.png)

# ByteBrew: Distributed Deception Security Platform

> **A containerized, config-driven honeypot architecture for distributed threat intelligence.**

## Overview

ByteBrew is not just a script; it is a **Distributed Deception Platform**. It decouples the **Deception Agent** (the trap) from the **Control Plane** (the analysis). This allows security teams to deploy lightweight agents across hundreds of servers while managing intelligence from a single dashboard.

### Architecture

The system follows a microservices approach:

1. **The Agent (Edge):** A lightweight Docker container that mimics SSH/HTTP services. It captures attack payloads and forwards them asynchronously.
2. **The Controller (Core):** An orchestration layer (powered by n8n/Python) that receives events, enriches IP data, and stores logs.
3. **The Dashboard (UI):** A visualization layer for real-time threat monitoring.

---

## Quick Start (Deploy in 30 Seconds)

### Prerequisite

- Docker & Docker Compose installed.

### 1. Run the Control Plane (Central Server)

```bash
cd controller
docker-compose up -d
```

_Dashboards are now accessible at `http://localhost:3000`_

### 2. Deploy a Deception Agent (Victim Server)

You can run an agent on _any_ machine (cloud VPS, local VM, on-prem) with a single command:

```bash
docker run -d \
  --name bytebrew-agent \
  -e CONTROLLER_URL="http://YOUR_CONTROLLER_IP:5000" \
  bytebrew/agent:latest
```

---

## Configuration

ByteBrew is **Config-Driven**. You do not need to change code to change the trap. Modify `config.yml`:

```yaml
services:
  ssh:
    enabled: true
    port: 2222
    banner: "Welcome to Internal Secure Server v2.1"
  http:
    enabled: false

logging:
  remote_logging: true
  verbosity: high
```

## Technology Stack

- **Agent:** Python, Paramiko (SSH), Flask (Web Trap), Docker
- **Controller:** n8n (Automation), PostgreSQL
- **Frontend:** HTML5, TailwindCSS, Chart.js

---

## 🤝 Contributing

This project is open-source. Pull requests are welcome for new deception modules (e.g., FTP, SQL traps).
