# LLMOAS

## Project Structure Overview

This repository contains three main folders, each serving a distinct purpose:

### `fastMCP-POC`
Generator and reference implementation for FastMCP servers. Includes scripts, authentication providers, and utilities for spinning up and managing FastMCP server instances, which act as secure, policy-driven API gateways or proxies.

### `mcp-llm`
Mock downstream API service simulating an e-commerce shop. Used for testing and development, allowing FastMCP servers and clients to interact with a realistic backend that mimics product, user, and basket endpoints.

### `nextjs-ai-chatbot`
Custom LLM agent interface and backend logic. Provides a Next.js and Quart based web interface and server-side code for connecting FastMCP clients to FastMCP servers, enabling interactive chat and agent-based workflows with LLMs.

