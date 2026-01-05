---
layout: default
title: "Developer Guide"
nav_order: 3
has_children: true
---




# Getting Started with Engram

Welcome to Engram! This guide will help you get up and running quickly.

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/zimaxnet/engram.git
   cd engram
   ```

2. **Set up local development**
   - [Local Setup Guide](setup/local-setup.md)
   - [Secrets Configuration](secrets-setup.md)

3. **Run the platform**

   ```bash
   docker-compose up -d
   open http://localhost:5173
   ```

## What is Engram?

Engram is an **enterprise-grade AI platform** that solves the Memory Wall Problem through innovative context engineering. Built on the **Brain + Spine** architecture pattern, Engram provides:

- 🧠 **Context Engineering** - 4-layer enterprise context schema
- 🦴 **Durable Workflows** - Temporal-based orchestration
- 💾 **Temporal Knowledge Graph** - Zep + Graphiti for memory
- 🚦 **System Navigator** - Unified UI for memory exploration
- 🎤 **Voice Interaction** - Azure VoiceLive with real-time audio
- 🔐 **Enterprise Security** - Entra ID authentication with RBAC

## Learning Path

### For Developers

1. [Local Setup](setup/local-setup.md) - Get your development environment ready
2. [Development Guides](../development/guides/) - Learn how to contribute
3. [Testing Guide](../development/testing/TESTING-GUIDE.md) - Run and write tests

### For Architects

1. [Architecture Overview](../architecture/) - Understand the Brain + Spine pattern
2. [4-Layer Context Schema](../architecture/context-schema/) - Learn about context engineering
3. [Security Context](../architecture/context-schema/security-context-enterprise-architecture.md) - Enterprise security architecture

### For Operators

1. [Deployment Guide](../deployment/) - Deploy to production
2. [Operations Guide](../operations/) - Monitor and troubleshoot
3. [Troubleshooting](../operations/troubleshooting/) - Common issues and solutions

## Next Steps

- 📖 [Architecture Deep Dive](../architecture/)
- 🤖 [Agent Personas](../agents/)
- 🚀 [Deployment Guide](../deployment/)
- 🔧 [Development Guide](../development/)

---

**Need Help?** Check out the [Troubleshooting Guide](../operations/troubleshooting/) or [open an issue](https://github.com/zimaxnet/engram/issues).
