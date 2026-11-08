---
id: "engineering-openai-structured-outputs"
title: "Structured Outputs"
topic: "engineering"
source_url: "https://platform.openai.com/docs/guides/structured-outputs"
author: "OpenAI"
date: "2024-08"
license: "官方文档(本地演示)"
tags: [结构化输出, JSON Schema]
---

For the complete documentation index, see [llms.txt](https://developers.openai.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL. 

[![Image 1: OpenAI Developers](https://developers.openai.com/OpenAI_Developers.svg)ChatGPT](https://developers.openai.com/)

Start searching

[API Dashboard](https://platform.openai.com/login)

[Try ChatGPT](https://chatgpt.com/)

Theme Light   Dark   System  

[Home](https://developers.openai.com/)

[API](https://developers.openai.com/api/docs)

[Overview Get started with the OpenAI API](https://developers.openai.com/api/docs)[Models Explore models and compare capabilities](https://developers.openai.com/api/docs/models)[Agents Build persistent agents on hosted infrastructure](https://developers.openai.com/api/docs/guides/agents)[Tools Connect models to tools and data](https://developers.openai.com/api/docs/guides/tools)[Audio & voice Build speech and realtime voice experiences](https://developers.openai.com/api/docs/guides/audio)[Production Deploy and scale your API integrations](https://developers.openai.com/api/docs/guides/production-best-practices)[API reference Explore endpoints, parameters, and responses](https://developers.openai.com/api/reference/overview)

[ChatGPT](https://developers.openai.com/chatgpt)

[Plugins Extend ChatGPT and Codex](https://developers.openai.com/plugins)[Sign in with ChatGPT Apps powered by your user's ChatGPT plan](https://developers.openai.com/siwc)[Commerce Build commerce flows in ChatGPT](https://developers.openai.com/commerce)[Ads Publish and measure ads in ChatGPT](https://developers.openai.com/ads)[Workspace Agents Trigger published ChatGPT workspace agents](https://developers.openai.com/workspace-agents)[ChatGPT + Codex user docs Guides and product docs for ChatGPT and Codex](https://learn.chatgpt.com/docs)[Use cases Example workflows and tasks teams can take on with ChatGPT or Codex](https://learn.chatgpt.com/use-cases)

[Docs](https://developers.openai.com/codex)

[Use cases](https://developers.openai.com/codex/use-cases)

[Training](https://developers.openai.com/training)

[Resources](https://developers.openai.com/codex/resources)

[Resources](https://developers.openai.com/learn)

[Showcase Demo apps to get inspired](https://developers.openai.com/showcase)[Blog Learnings and experiences from developers](https://developers.openai.com/blog)[Cookbook Notebook examples for building with OpenAI models](https://developers.openai.com/cookbook)[Learn Docs, videos, and demo apps for building with OpenAI](https://developers.openai.com/learn)[Community Programs, meetups, and support for builders](https://developers.openai.com/community)

[Overview](https://developers.openai.com/api/docs)[Models](https://developers.openai.com/api/docs/models)[Agents](https://developers.openai.com/api/docs/guides/agents)[Tools](https://developers.openai.com/api/docs/guides/tools)[Audio & voice](https://developers.openai.com/api/docs/guides/audio)[Production](https://developers.openai.com/api/docs/guides/production-best-practices)[API reference](https://developers.openai.com/api/reference/overview)

## Search the API docs

Search docs 

### Suggested

responses create reasoning_effort realtime prompt caching

 Primary navigation 

 API  ChatGPT  Docs  Use cases  Training  Resources  Resources 

Theme Light   Dark   System  

Search docs 

### Suggested

responses create reasoning_effort realtime prompt caching

 Overview  Models  Agents  Tools  Audio & voice  Production  API reference 

Docs Models

*   [Home](https://developers.openai.com/api/docs)

### Get started

*   [Quickstart](https://developers.openai.com/api/docs/quickstart)
*   [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model)
*   [Key concepts](https://developers.openai.com/api/docs/concepts)
*   [API credits for ChatGPT subscribers](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)

### Core concepts

*   [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
*   [Decisions API](https://developers.openai.com/api/docs/guides/decisions)
*   [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
*   [Background mode](https://developers.openai.com/api/docs/guides/background)
*   [Streaming](https://developers.openai.com/api/docs/guides/streaming-responses)
*   [WebSocket mode](https://developers.openai.com/api/docs/guides/websocket-mode)
*   [Mid-turn steering](https://developers.openai.com/api/docs/guides/steering)
*   [Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent)
*   [Webhooks](https://developers.openai.com/api/docs/guides/webhooks)
*   [File inputs](https://developers.openai.com/api/docs/guides/file-inputs)
*   [Compaction](https://developers.openai.com/api/docs/guides/compaction)
*   [Counting tokens](https://developers.openai.com/api/docs/guides/token-counting)

### SDKs and CLI

*   [OpenAI SDK](https://developers.openai.com/api/docs/libraries)
*   [OpenAI CLI](https://developers.openai.com/api/docs/libraries/openai-cli)

### Resources

*   [Changelog](https://developers.openai.com/api/docs/changelog)
*   [Deprecations](https://developers.openai.com/api/docs/deprecations)
*   [Supported countries](https://developers.openai.com/api/docs/supported-countries)
*   [OpenAI Crawlers](https://developers.openai.com/api/docs/bots)
*   [Terms and policies](https://openai.com/policies)

### Legacy APIs

*   
Agent Builder
    *   [Overview](https://developers.openai.com/api/docs/guides/agent-builder)
    *   [Migration guide](https://developers.openai.com/api/docs/guides/agent-builder/migrate-from-agent-builder)
    *   [Node reference](https://developers.openai.com/api/docs/guides/node-reference)
    *   [Safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety)

*   
Evals
    *   [Getting started](https://developers.openai.com/api/docs/guides/evaluation-getting-started)
    *   [Working with evals](https://developers.openai.com/api/docs/guides/evals)
    *   [Prompt optimizer](https://developers.openai.com/api/docs/guides/prompt-optimizer)
    *   [External models](https://developers.openai.com/api/docs/guides/external-models)
    *   [Graders](https://developers.openai.com/api/docs/guides/graders)

*   
Fine-tuning
    *   [Optimization cycle](https://developers.openai.com/api/docs/guides/model-optimization)
    *   [Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning)
    *   [Vision fine-tuning](https://developers.openai.com/api/docs/guides/vision-fine-tuning)
    *   [Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization)
    *   [Best practices](https://developers.openai.com/api/docs/guides/fine-tuning-best-practices)

*   
Assistants API
    *   [Migration guide](https://developers.openai.com/api/docs/assistants/migration)

*   [Model catalog](https://developers.openai.com/api/docs/models)

### Choose a model

*   [Pricing](https://developers.openai.com/api/docs/pricing)
*   [Model selection](https://developers.openai.com/api/docs/guides/model-selection)

### Text and code

*   [Text generation](https://developers.openai.com/api/docs/guides/text)
*   [Code generation](https://developers.openai.com/api/docs/guides/code-generation)
*   [Structured output](https://developers.openai.com/api/docs/guides/structured-outputs)

### Prompting

*   [Overview](https://developers.openai.com/api/docs/guides/prompting)
*   [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
*   [Citation formatting](https://developers.openai.com/api/docs/guides/citation-formatting)
*   [Migration guide](https://developers.openai.com/api/docs/guides/prompting/migrate-from-prompt-object)
*   [Prompt generation](https://developers.openai.com/api/docs/guides/prompt-generation)
*   [Frontend prompting](https://developers.openai.com/api/docs/guides/frontend-prompt)

### Reasoning

*   [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
*   [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)

### Images

*   
[Images and vision](https://developers.openai.com/api/docs/guides/images-vision)
    *   [Image input cost calculator](https://developers.openai.com/api/docs/guides/image-cost-calculator)

*   
[Image generation](https://developers.openai.com/api/docs/guides/image-generation)
    *   [Overview](https://developers.openai.com/api/docs/guides/image-generation)
    *   [Image prompting](https://developers.openai.com/api/docs/guides/image-prompting)

### Realtime and audio

*   [Audio and speech](https://developers.openai.com/api/docs/guides/audio)
*   [Getting started](https://developers.openai.com/api/docs/guides/realtime)
*   [Voice agents](https://developers.openai.com/api/docs/guides/voice-agents)

### Specialized models

*   [Embeddings](https://developers.openai.com/api/docs/guides/embeddings)
*   [Moderation](https://developers.openai.com/api/docs/guides/moderation)

*   [Overview](https://developers.openai.com/api/docs/guides/agents)

### Agents API

*   [Overview](https://developers.openai.com/api/docs/guides/agents-api/overview)
*   [Quickstart](https://developers.openai.com/api/docs/guides/agents-api/quickstart)
*   [Architecture](https://developers.openai.com/api/docs/guides/agents-api/architecture)
*   [Configuring Agents](https://developers.openai.com/api/docs/guides/agents-api/configuration)
*   
Sessions
    *   [Run and continue sessions](https://developers.openai.com/api/docs/guides/agents-api/sessions)
    *   [Events and items](https://developers.openai.com/api/docs/guides/agents-api/sessions/events)
    *   [Manage sessions](https://developers.openai.com/api/docs/guides/agents-api/sessions/manage)
    *   [Scheduled automations](https://developers.openai.com/api/docs/guides/agents-api/sessions/automations)
    *   [Automatic review](https://developers.openai.com/api/docs/guides/agents-api/sessions/approvals)
    *   [Webhooks](https://developers.openai.com/api/docs/guides/agents-api/sessions/webhooks)

*   
Environments and sandboxes
    *   [OpenAI-hosted sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted)
    *   [Self-hosted sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted)
    *   [Sandbox lifecycle](https://developers.openai.com/api/docs/guides/agents-api/environments/lifecycle)
    *   [Pre-warm sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/prewarmed)
    *   [Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)
    *   [Files and artifacts](https://developers.openai.com/api/docs/guides/agents-api/environments/files)

*   
Tools and integrations
    *   [Web search](https://developers.openai.com/api/docs/guides/agents-api/tools/web-search)
    *   [Computer use](https://developers.openai.com/api/docs/guides/agents-api/tools/computer-use)
    *   [Functions](https://developers.openai.com/api/docs/guides/agents-api/tools/functions)
    *   [MCP connections](https://developers.openai.com/api/docs/guides/agents-api/tools/mcp)
    *   [Plugins](https://developers.openai.com/api/docs/guides/agents-api/tools/plugins)
    *   [Vaults](https://developers.openai.com/api/docs/guides/agents-api/tools/vaults)

*   [Multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent)
*   [Observability and usage](https://developers.openai.com/api/docs/guides/agents-api/observability)
*   [Tracing](https://developers.openai.com/api/docs/guides/agents-api/tracing)
*   [Errors and recovery](https://developers.openai.com/api/docs/guides/agents-api/errors)
*   [API reference](https://developers.openai.com/api/reference/resources/beta/subresources/agents)
*   [Bedrock Managed Agents](https://developers.openai.com/api/docs/guides/agents-api/bedrock-managed-agents)

### Agents SDK

*   [Overview](https://developers.openai.com/api/docs/guides/agents/sdk)
*   [Quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart)
*   [Agent definitions](https://developers.openai.com/api/docs/guides/agents/define-agents)
*   [Models and providers](https://developers.openai.com/api/docs/guides/agents/models)
*   [Running agents](https://developers.openai.com/api/docs/guides/agents/running-agents)
*   [Sandbox agents](https://developers.openai.com/api/docs/guides/agents/sandboxes)
*   [Orchestration](https://developers.openai.com/api/docs/guides/agents/orchestration)
*   [Guardrails](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)
*   [Results and state](https://developers.openai.com/api/docs/guides/agents/results)
*   [Integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)
*   [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals)

### ChatKit

*   [Overview](https://developers.openai.com/api/docs/guides/chatkit)
*   [Customize](https://developers.openai.com/api/docs/guides/chatkit-themes)
*   [Widgets](https://developers.openai.com/api/docs/guides/chatkit-widgets)
*   [Actions](https://developers.openai.com/api/docs/guides/chatkit-actions)
*   [Advanced integrations](https://developers.openai.com/api/docs/guides/custom-chatkit)

*   [Overview](https://developers.openai.com/api/docs/guides/tools)
*   [Function calling](https://developers.openai.com/api/docs/guides/function-calling)

### Search and retrieval

*   [Web search](https://developers.openai.com/api/docs/guides/tools-web-search)
*   [File search](https://developers.openai.com/api/docs/guides/tools-file-search)
*   [Retrieval](https://developers.openai.com/api/docs/guides/retrieval)

### Connect tools and data

*   [MCP servers](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
*   [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

### Build tool workflows

*   [Skills](https://developers.openai.com/api/docs/guides/tools-skills)
*   [Tool search](https://developers.openai.com/api/docs/guides/tools-tool-search)
*   [Programmatic tool calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling)
*   [Async tool calling](https://developers.openai.com/api/docs/guides/async-tool-calling)

### Computer and code

*   [Shell](https://developers.openai.com/api/docs/guides/tools-shell)
*   
[Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use)
    *   [Integration recipes](https://developers.openai.com/api/docs/guides/tools-computer-use-integration)
    *   [Driver reference](https://developers.openai.com/api/docs/guides/tools-computer-use-sdk-drivers)

*   [Apply Patch](https://developers.openai.com/api/docs/guides/tools-apply-patch)
*   [Code interpreter](https://developers.openai.com/api/docs/guides/tools-code-interpreter)

### Media

*   [Image generation](https://developers.openai.com/api/docs/guides/tools-image-generation)

*   [Overview](https://developers.openai.com/api/docs/guides/audio)

### GPT-Live

*   [Getting started](https://developers.openai.com/api/docs/guides/live)
*   [Prompting](https://developers.openai.com/api/docs/guides/live-prompting)
*   [Managing sessions](https://developers.openai.com/api/docs/guides/live-conversations)
*   [Delegation and tools](https://developers.openai.com/api/docs/guides/live-delegation)
*   [Migrate to GPT-Live](https://developers.openai.com/api/docs/guides/live-migration)
*   [Partner integrations](https://developers.openai.com/api/docs/guides/live-partner-integrations)

### Realtime API

*   [Getting started](https://developers.openai.com/api/docs/guides/realtime)
*   [Prompting](https://developers.openai.com/api/docs/guides/voice-prompting)
*   [Managing conversations](https://developers.openai.com/api/docs/guides/realtime-conversations)
*   [Voice activity detection](https://developers.openai.com/api/docs/guides/realtime-vad)
*   [Tools and MCP](https://developers.openai.com/api/docs/guides/realtime-mcp)

### Build with voice

*   [Voice agents](https://developers.openai.com/api/docs/guides/voice-agents)
*   [Connect voice to Decisions](https://developers.openai.com/api/docs/guides/decisions-voice)
*   [Custom voices](https://developers.openai.com/api/docs/guides/custom-voices)
*   [Cost optimization](https://developers.openai.com/api/docs/guides/voice-latency-cost)

### Connections

*   [WebRTC](https://developers.openai.com/api/docs/guides/voice-webrtc)
*   [WebRTC with WARP](https://developers.openai.com/api/docs/guides/realtime-webrtc-warp)
*   [WebSockets](https://developers.openai.com/api/docs/guides/voice-websockets)
*   [Telephony and SIP](https://developers.openai.com/api/docs/guides/voice-sip)
*   [Server-side controls](https://developers.openai.com/api/docs/guides/voice-server-controls)

### Audio processing

*   [File transcription](https://developers.openai.com/api/docs/guides/speech-to-text)
*   [Live transcription](https://developers.openai.com/api/docs/guides/realtime-transcription)
*   [Live translation](https://developers.openai.com/api/docs/guides/realtime-translation)
*   [Text to speech](https://developers.openai.com/api/docs/guides/text-to-speech)
*   [Audio in Chat Completions](https://developers.openai.com/api/docs/guides/audio-chat-completions)

### Go live

*   [Production best practices](https://developers.openai.com/api/docs/guides/production-best-practices)
*   [API keys and service accounts](https://developers.openai.com/api/docs/guides/api-keys)
*   [Deployment checklist](https://developers.openai.com/api/docs/guides/deployment-checklist)

### Performance and quality

*   [Fast mode](https://developers.openai.com/api/docs/guides/fast-mode)
*   [Ultrafast mode](https://developers.openai.com/api/docs/guides/ultrafast-mode)
*   [Latency optimization](https://developers.openai.com/api/docs/guides/latency-optimization)
*   [Predicted Outputs](https://developers.openai.com/api/docs/guides/predicted-outputs)
*   [Accuracy optimization](https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy)

### Evaluation

*   [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
*   [Promptfoo](https://developers.openai.com/api/docs/guides/promptfoo-codex)

### Cost and throughput

*   [Cost optimization](https://developers.openai.com/api/docs/guides/cost-optimization)
*   
[Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
    *   [Prompt cache diagnostics](https://developers.openai.com/api/docs/guides/prompt-caching/diagnostics)

*   [Batch](https://developers.openai.com/api/docs/guides/batch)
*   [Flex processing](https://developers.openai.com/api/docs/guides/flex-processing)

### Safety and governance

*   [Safety best practices](https://developers.openai.com/api/docs/guides/safety-best-practices)
*   [Red teaming](https://developers.openai.com/api/docs/guides/red-teaming)
*   [Daybreak](https://developers.openai.com/api/docs/guides/daybreak)
*   
Safety checks
    *   [Safety classifiers](https://developers.openai.com/api/docs/guides/safety-checks)
    *   [Cybersecurity checks](https://developers.openai.com/api/docs/guides/safety-checks/cybersecurity)
    *   [Misalignment monitoring](https://developers.openai.com/api/docs/guides/safety-checks/misalignment-monitoring)

*   [Enforcement notifications](https://developers.openai.com/api/docs/guides/safety-enforcement)
*   [Under-18 guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance)
*   [CSAM guidance](https://developers.openai.com/api/docs/guides/csam-guidance)
*   [Content provenance](https://developers.openai.com/api/docs/guides/content-provenance)
*   [Your data](https://developers.openai.com/api/docs/guides/your-data)
*   [Private Safety Processing](https://developers.openai.com/api/docs/guides/private-safety-processing)
*   [Permissions](https://developers.openai.com/api/docs/guides/rbac)

### Infrastructure and access

*   
[Terraform provider](https://developers.openai.com/api/docs/guides/terraform)
    *   [Overview](https://developers.openai.com/api/docs/guides/terraform)
    *   [Projects and access](https://developers.openai.com/api/docs/guides/terraform/projects-and-access)
    *   [Service accounts](https://developers.openai.com/api/docs/guides/terraform/service-accounts)
    *   [Rate limits and spend](https://developers.openai.com/api/docs/guides/terraform/rate-limits-and-spend)
    *   [Model, tool, and data controls](https://developers.openai.com/api/docs/guides/terraform/project-controls)
    *   [Import and reconciliation](https://developers.openai.com/api/docs/guides/terraform/import-and-reconcile)

*   [Private Link](https://developers.openai.com/api/docs/guides/private-link)
*   [IP allowlist](https://developers.openai.com/api/docs/guides/ip-allowlist)
*   [Organization blocking](https://developers.openai.com/api/docs/guides/organization-blocking)
*   [Mutual TLS](https://developers.openai.com/api/docs/guides/mutual-tls)
*   
[Workload identity federation](https://developers.openai.com/api/docs/guides/workload-identity-federation)
    *   [Federation rules](https://developers.openai.com/api/docs/guides/workload-identity-federation/federation-rules)
    *   [X.509 certificates](https://developers.openai.com/api/docs/guides/workload-identity-federation/x509)
    *   [Kubernetes](https://developers.openai.com/api/docs/guides/workload-identity-federation/kubernetes)
    *   [AWS](https://developers.openai.com/api/docs/guides/workload-identity-federation/aws)
    *   [Microsoft Azure](https://developers.openai.com/api/docs/guides/workload-identity-federation/microsoft-azure)
    *   [Google Cloud](https://developers.openai.com/api/docs/guides/workload-identity-federation/google-cloud)
    *   [Oracle Cloud Infrastructure](https://developers.openai.com/api/docs/guides/workload-identity-federation/oracle-cloud)
    *   [GitHub Actions](https://developers.openai.com/api/docs/guides/workload-identity-federation/github-actions)
    *   [SPIFFE](https://developers.openai.com/api/docs/guides/workload-identity-federation/spiffe)
    *   [Idira](https://developers.openai.com/api/docs/guides/workload-identity-federation/idira)

*   [IP egress ranges](https://developers.openai.com/api/docs/guides/ip-addresses)
*   [Amazon Bedrock](https://developers.openai.com/api/docs/guides/amazon-bedrock)

### Operations

*   [Rate limits](https://developers.openai.com/api/docs/guides/rate-limits)
*   [Spend limits](https://developers.openai.com/api/docs/guides/spend-limits)
*   [Admin APIs](https://developers.openai.com/api/docs/guides/admin-apis)
*   [Error codes](https://developers.openai.com/api/docs/guides/error-codes)

[Overview](https://developers.openai.com/chatgpt) Plugins  Sign in with ChatGPT  Commerce  Ads  Workspace Agents [ChatGPT + Codex user docs](https://learn.chatgpt.com/docs)[Use cases](https://learn.chatgpt.com/use-cases)

Docs Overview

*   [Home](https://developers.openai.com/plugins)
*   [Quickstart](https://developers.openai.com/plugins/quickstart)

### Core concepts

*   [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins)
*   [Skills](https://developers.openai.com/plugins/concepts/skills)
*   [MCP server](https://developers.openai.com/plugins/concepts/mcp-server)

### Plan

*   [Brainstorm use cases](https://developers.openai.com/plugins/plan/use-case)
*   [Define tools](https://developers.openai.com/plugins/plan/tools)

### Build

*   [Build an MCP server](https://developers.openai.com/plugins/build/mcp-server)
*   [Add UI to your MCP server (optional)](https://developers.openai.com/plugins/build/chatgpt-ui)
*   [Add events to your MCP server (optional)](https://developers.openai.com/plugins/build/mcp-events)
*   [Extensions](https://developers.openai.com/plugins/build/extensions)
*   [Authenticate users](https://developers.openai.com/plugins/build/auth)
*   [Build skills](https://developers.openai.com/plugins/build/skills)
*   [Package your plugin](https://developers.openai.com/plugins/build/plugins)
*   [Examples](https://developers.openai.com/plugins/build/examples)

### Test and publish

*   [Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
*   [Submit and publish](https://developers.openai.com/plugins/deploy/submission)
*   [Submit desktop-only plugins](https://developers.openai.com/plugins/deploy/desktop-only)
*   [Submission error reference](https://developers.openai.com/plugins/deploy/submission-errors)

### Conversion specs

*   [Restaurant reservation spec](https://developers.openai.com/plugins/guides/restaurant-reservation-conversion-spec)
*   [Get Quote spec](https://developers.openai.com/plugins/guides/local-services-request-quote-conversion-spec)
*   [Product checkout spec](https://developers.openai.com/plugins/guides/product-checkout-conversion-spec)

### Guides

*   [UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines)
*   [Optimize Metadata](https://developers.openai.com/plugins/guides/optimize-metadata)
*   [Submit a Claude Code plugin](https://developers.openai.com/plugins/guides/submit-claude-plugin)
*   [Security & Privacy](https://developers.openai.com/plugins/guides/security-privacy)
*   [Troubleshooting](https://developers.openai.com/plugins/deploy/troubleshooting)

### Resources

*   [Changelog](https://developers.openai.com/plugins/changelog)
*   [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)
*   [MCP server review requirements](https://developers.openai.com/plugins/deploy/app-review)
*   [Plugin UI reference](https://developers.openai.com/plugins/reference)
*   [Checkout API reference](https://developers.openai.com/plugins/build/monetization)

*   [Home](https://developers.openai.com/siwc)
*   [Quickstart](https://developers.openai.com/siwc/quickstart)
*   [Request a client ID](https://developers.openai.com/siwc/request-client-id)

### Identity

*   [On your website](https://developers.openai.com/siwc/website)
*   [In your ChatGPT plugin](https://developers.openai.com/siwc/chatgpt-plugin)
*   [Account security notification](https://developers.openai.com/siwc/account-security-notification)

### ChatGPT plan usage

*   [Overview](https://developers.openai.com/siwc/token-sharing-open-source)
*   [UI/UX guidelines](https://developers.openai.com/siwc/ui-ux-guidelines)
*   [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
*   [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)
*   [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
*   [Codex app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)
*   [Self-hosted VMs](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms)
*   [Token reference](https://developers.openai.com/siwc/token-sharing-open-source/token-reference)
*   [Errors and recovery](https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery)
*   [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

*   [Home](https://developers.openai.com/commerce)

### Guides

*   [Get started](https://developers.openai.com/commerce/guides/get-started)
*   [Best practices](https://developers.openai.com/commerce/guides/best-practices)

### File Upload

*   [Overview](https://developers.openai.com/commerce/specs/file-upload/overview)
*   [Products](https://developers.openai.com/commerce/specs/file-upload/products)

### API

*   [Overview](https://developers.openai.com/commerce/specs/api/overview)
*   [Feeds](https://developers.openai.com/commerce/specs/api/feeds)
*   [Products](https://developers.openai.com/commerce/specs/api/products)
*   [Promotions](https://developers.openai.com/commerce/specs/api/promotions)

*   [Ads Overview](https://developers.openai.com/ads)

### Measurement

*   [Measurement Pixel](https://developers.openai.com/ads/measurement-pixel)
*   [Multiple Pixels (Advanced)](https://developers.openai.com/ads/multiple-pixels)
*   [Image Tag](https://developers.openai.com/ads/image-tag)
*   [Conversions API](https://developers.openai.com/ads/conversions-api)
*   [Supported Events](https://developers.openai.com/ads/supported-events)

### Advertiser API

*   [Overview](https://developers.openai.com/ads/api-overview)
*   [API Partner Setup](https://developers.openai.com/ads/api-partner-setup)
*   [Campaign Management](https://developers.openai.com/ads/campaign-management)
*   [Bidding & Budgets](https://developers.openai.com/ads/bidding-and-budgets)
*   [Targeting](https://developers.openai.com/ads/campaign-targeting)
*   [Product Feeds](https://developers.openai.com/ads/product-feeds)
*   [Hotel Feeds (limited beta)](https://developers.openai.com/ads/hotel-feeds)
*   [Conversion Tracking](https://developers.openai.com/ads/conversion-tracking)
*   [Reporting](https://developers.openai.com/ads/reporting)
*   [Troubleshooting](https://developers.openai.com/ads/troubleshooting)
*   [Account Management](https://developers.openai.com/ads/account-management)

### API Reference

*   [Authentication](https://developers.openai.com/ads/api-reference/authentication)
*   [Ad Account](https://developers.openai.com/ads/api-reference/ad-account)
*   [Audit Logs](https://developers.openai.com/ads/api-reference/audit-logs)
*   [Campaigns](https://developers.openai.com/ads/api-reference/campaigns)
*   [Ad Groups](https://developers.openai.com/ads/api-reference/ad-groups)
*   [Ads](https://developers.openai.com/ads/api-reference/ads)
*   [Insights](https://developers.openai.com/ads/api-reference/insights)
*   [Files](https://developers.openai.com/ads/api-reference/files)
*   [Conversion Setup](https://developers.openai.com/ads/api-reference/conversion-setup)

*   [Home](https://developers.openai.com/workspace-agents)

### Get started

*   [Trigger workspace agent runs](https://developers.openai.com/workspace-agents/trigger-runs)
*   [Authenticate with Workspace Agent access tokens](https://developers.openai.com/workspace-agents/authentication)

 Overview  Features  Configuration  Developers  Security  Administration  Use Cases  Resources 

Docs Overview

*   [Home](https://developers.openai.com/codex)

### Get started

*   [Quickstart](https://developers.openai.com/codex/quickstart)
*   [Use ChatGPT](https://developers.openai.com/codex/use-chatgpt)
*   [Get started with Work](https://developers.openai.com/codex/get-started-with-work)
*   [Meet dots](https://developers.openai.com/codex/dots?nav=overview)
*   [Import from another agent](https://developers.openai.com/codex/import)

### Foundations

*   [Prompting](https://developers.openai.com/codex/prompting)
*   [Working with agents](https://developers.openai.com/codex/working-with-agents)
*   [Model selection](https://developers.openai.com/codex/model-selection)
*   [Personalize ChatGPT](https://developers.openai.com/codex/personalize)
*   [Skills & Plugins](https://developers.openai.com/codex/skills-and-plugins)
*   [Permissions](https://developers.openai.com/codex/permission-modes)

### Explore

*   [What's new](https://developers.openai.com/codex/whats-new)
*   [Models](https://developers.openai.com/codex/models)
*   [Pricing](https://developers.openai.com/codex/pricing)
*   [Glossary](https://developers.openai.com/codex/glossary)

### Available on

*   [ChatGPT desktop app](https://developers.openai.com/codex/app)
*   [ChatGPT mobile app](https://developers.openai.com/codex/mobile)
*   [ChatGPT on the web](https://developers.openai.com/codex/web)
*   [Codex CLI](https://developers.openai.com/codex/cli)
*   [Codex IDE extension](https://developers.openai.com/codex/ide)
*   [Codex Cloud](https://developers.openai.com/codex/cloud)

### Releases

*   [Changelog](https://developers.openai.com/codex/changelog)
*   [Feature Maturity](https://developers.openai.com/codex/feature-maturity)
*   [Open Source](https://developers.openai.com/codex/open-source)

*   [Overview](https://developers.openai.com/codex/features)

### Workflows

*   [Projects and chats](https://developers.openai.com/codex/projects)
*   [Build plugins](https://developers.openai.com/codex/build-plugins)
*   [Visualizations](https://developers.openai.com/codex/visualizations)
*   [Scheduled tasks](https://developers.openai.com/codex/automations)
*   [Long-running work](https://developers.openai.com/codex/long-running-work)
*   [Notifications](https://developers.openai.com/codex/notifications)
*   [Pets](https://developers.openai.com/codex/pets)
*   [Codex Micro](https://developers.openai.com/codex/features/codex-micro)

### Capabilities

*   [Browser](https://developers.openai.com/codex/browser)
*   [Computer use](https://developers.openai.com/codex/computer-use)
*   [Voice](https://developers.openai.com/codex/features/voice)
*   [Composer Predictions](https://developers.openai.com/codex/features/composer-predictions)
*   [Plugins](https://developers.openai.com/codex/plugins)
*   [Sign in with ChatGPT](https://developers.openai.com/codex/sign-in-with-chatgpt)
*   [Web search](https://developers.openai.com/codex/web-search)
*   [Image generation](https://developers.openai.com/codex/image-generation)
*   [Image inputs](https://developers.openai.com/codex/image-inputs)
*   [Appshots](https://developers.openai.com/codex/appshots)
*   [Browser extension](https://developers.openai.com/codex/chrome-extension)
*   [Work with files](https://developers.openai.com/codex/artifacts-viewer)

### Sites

*   [Overview](https://developers.openai.com/codex/sites)
*   [Create a site](https://developers.openai.com/codex/sites/creating-a-site)
*   [Data and connections](https://developers.openai.com/codex/sites/data-and-connections)
*   [Publish and share](https://developers.openai.com/codex/sites/publishing-and-sharing)
*   [Manage a site](https://developers.openai.com/codex/sites/managing-a-site)

### dots

*   [Meet dots](https://developers.openai.com/codex/dots?nav=features)
*   [Getting started](https://developers.openai.com/codex/dots/getting-started)
*   [Messaging](https://developers.openai.com/codex/dots/channels)
*   [Tasks and memory](https://developers.openai.com/codex/dots/tasks-and-memory)
*   [Computers and apps](https://developers.openai.com/codex/dots/computers-and-apps)
*   [Controls](https://developers.openai.com/codex/dots/controls)

### ChatGPT Space

*   [Overview](https://developers.openai.com/codex/space)
*   [Getting started](https://developers.openai.com/codex/space/getting-started)
*   [Pages](https://developers.openai.com/codex/space/pages)
*   [Work with agents](https://developers.openai.com/codex/space/agents)
*   [Collaboration](https://developers.openai.com/codex/space/collaboration)

### Reference

*   [Commands](https://developers.openai.com/codex/reference/commands)
*   [Slash commands](https://developers.openai.com/codex/reference/slash-commands)
*   [Settings](https://developers.openai.com/codex/reference/settings)
*   [Troubleshooting](https://developers.openai.com/codex/reference/troubleshooting)

*   [Overview](https://developers.openai.com/codex/configuration)

### Customization

*   [Overview](https://developers.openai.com/codex/customization/overview)
*   [Memories](https://developers.openai.com/codex/customization/memories)
*   [Computer History](https://developers.openai.com/codex/customization/computer-history)

### Config file

*   [Config Basics](https://developers.openai.com/codex/config-file/config-basic)
*   [Advanced Config](https://developers.openai.com/codex/config-file/config-advanced)
*   [Config Reference](https://developers.openai.com/codex/config-file/config-reference)
*   [Environment Variables](https://developers.openai.com/codex/config-file/environment-variables)
*   [Sample Config](https://developers.openai.com/codex/config-file/config-sample)

### Agent configuration

*   [AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md)
*   [Subagents](https://developers.openai.com/codex/agent-configuration/subagents)
*   [Speed](https://developers.openai.com/codex/agent-configuration/speed)
*   [Rules](https://developers.openai.com/codex/agent-configuration/rules)

### Extend ChatGPT and Codex

*   [Record & Replay](https://developers.openai.com/codex/extend/record-and-replay)
*   [MCP](https://developers.openai.com/codex/extend/mcp)

### Linux

*   [Desktop app](https://developers.openai.com/codex/linux/linux-app)

### Windows

*   [Desktop app](https://developers.openai.com/codex/windows/windows-app)
*   [Windows sandbox](https://developers.openai.com/codex/windows/windows-sandbox)
*   [WSL](https://developers.openai.com/codex/windows/wsl)

*   [Overview](https://developers.openai.com/codex/developers)

### Development workflows

*   [Code review](https://developers.openai.com/codex/code-review)
*   [Integrated terminal](https://developers.openai.com/codex/integrated-terminal)

### Extend and automate

*   [Build skills](https://developers.openai.com/codex/build-skills)
*   [Site tools (WebMCP)](https://developers.openai.com/codex/webmcp)
*   [Annotations Extensibility](https://developers.openai.com/codex/annotations-extensibility)
*   [Hooks](https://developers.openai.com/codex/hooks)

### Environments

*   [Modes](https://developers.openai.com/codex/environments/modes)
*   [Local environments](https://developers.openai.com/codex/environments/local-environment)
*   [Git worktrees](https://developers.openai.com/codex/environments/git-worktrees)

### Codex Cloud

*   [Cloud environments](https://developers.openai.com/codex/environments/cloud-environments)

### Build with Codex

*   [Codex SDK](https://developers.openai.com/codex/codex-sdk)
*   [App Server](https://developers.openai.com/codex/app-server)
*   [GitHub Action](https://developers.openai.com/codex/github-action)
*   [Non-interactive mode](https://developers.openai.com/codex/non-interactive-mode)

### Third-party integrations

*   [GitHub](https://developers.openai.com/codex/third-party/github)
*   [GitLab (Beta)](https://developers.openai.com/codex/third-party/gitlab)
*   [Slack](https://developers.openai.com/codex/third-party/slack)
*   [Linear](https://developers.openai.com/codex/third-party/linear)

### Reference

*   [CLI customization](https://developers.openai.com/codex/cli-customization)
*   [Developer commands](https://developers.openai.com/codex/developer-commands)
*   [Developer settings](https://developers.openai.com/codex/developer-settings)

*   [Overview](https://developers.openai.com/codex/security-administration)

### Permissions

*   [Profiles](https://developers.openai.com/codex/permissions)
*   [Sandboxing](https://developers.openai.com/codex/sandboxing)
*   [Auto-review](https://developers.openai.com/codex/sandboxing/auto-review)
*   [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)

### Codex Security

*   [Overview](https://developers.openai.com/codex/security)
*   
Codex Security Cloud
    *   [Setup](https://developers.openai.com/codex/security/setup)
    *   [Security Review](https://developers.openai.com/codex/security/security-review)
    *   [Improving the threat model](https://developers.openai.com/codex/security/threat-model)
    *   [FAQ](https://developers.openai.com/codex/security/faq)

*   
Codex Security plugin
    *   [Quickstart](https://developers.openai.com/codex/security/plugin)
    *   [Run a security scan](https://developers.openai.com/codex/security/plugin/scans)
    *   [Run a deep scan](https://developers.openai.com/codex/security/plugin/deep-scans)
    *   [Review code changes](https://developers.openai.com/codex/security/plugin/code-changes)
    *   [Use the Security workbench](https://developers.openai.com/codex/security/plugin/workbench)
    *   [Triage a backlog](https://developers.openai.com/codex/security/plugin/triage-backlog)
    *   [Fix findings](https://developers.openai.com/codex/security/plugin/fix-findings)
    *   [Propose security hardening](https://developers.openai.com/codex/security/plugin/security-hardening)
    *   [Write vulnerability reports](https://developers.openai.com/codex/security/plugin/vulnerability-reports)
    *   [Export and track findings](https://developers.openai.com/codex/security/plugin/export-findings)
    *   [Changelog](https://developers.openai.com/codex/security/plugin/changelog)

*   
Codex Security CLI
    *   [Quickstart](https://developers.openai.com/codex/security/cli)
    *   [Run bulk scans](https://developers.openai.com/codex/security/cli/bulk-scans)
    *   
CI/CD
        *   [Overview](https://developers.openai.com/codex/security/cli/ci)
        *   [GitHub Actions](https://developers.openai.com/codex/security/cli/ci/github)
        *   [GitLab CI/CD](https://developers.openai.com/codex/security/cli/ci/gitlab)

    *   [Reference](https://developers.openai.com/codex/security/cli/reference)
    *   [FAQ](https://developers.openai.com/codex/security/cli/faq)

*   [Codex Security SDK](https://developers.openai.com/codex/security/sdk)

### Cyber safety

*   [Models & Trusted Access](https://developers.openai.com/codex/cyber-safety)
*   [Recommended configuration](https://developers.openai.com/codex/cyber-safety/recommended-configuration)

*   [Overview](https://developers.openai.com/codex/administration)

### Getting started

*   [Admin rollout guide](https://developers.openai.com/codex/enterprise/admin-setup)
*   [Admin plugin](https://developers.openai.com/codex/enterprise/admin-plugin)

### Feature Configuration

*   [Dots](https://developers.openai.com/codex/enterprise/dots-admin-guide)
*   [Space](https://developers.openai.com/codex/space/collaboration#for-workspace-admins)
*   [Sites](https://developers.openai.com/codex/enterprise/sites)
*   [Teams and Team Tasks](https://developers.openai.com/codex/enterprise/teams#for-workspace-admins)
*   [ChatGPT in Slack and Teams](https://developers.openai.com/codex/enterprise/chatgpt-slack-and-teams)
*   [Workspace connections](https://developers.openai.com/codex/enterprise/shared-connections)
*   [Local computer access for Work Cloud and dots](https://developers.openai.com/codex/enterprise/cloud-local-access)

### Identity and access

*   [Authentication overview](https://developers.openai.com/codex/auth)
*   [Groups and provisioning](https://developers.openai.com/codex/enterprise/groups-and-provisioning)
*   [Dynamic groups](https://developers.openai.com/codex/enterprise/dynamic-groups)
*   [User lifecycle management](https://developers.openai.com/codex/enterprise/user-lifecycle)
*   [Roles and workspace permissions](https://developers.openai.com/codex/enterprise/roles-and-workspace-permissions)
*   [Personal access tokens](https://developers.openai.com/codex/enterprise/access-tokens)
*   [Service accounts](https://developers.openai.com/codex/enterprise/service-accounts)

### Configuration

*   [Windows app and CLI deployment](https://developers.openai.com/codex/enterprise/windows-deployment)
*   [NFS home directories](https://developers.openai.com/codex/environments/network-file-systems)
*   [Manage app updates](https://developers.openai.com/codex/enterprise/manage-app-updates)
*   
[Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration)
    *   [Self-host configuration](https://developers.openai.com/codex/enterprise/configuration-server)

*   [Codex security cookbook](https://developers.openai.com/codex/enterprise/security-cookbook)
*   [Remote connections](https://developers.openai.com/codex/remote-connections)
*   [Workspace model availability](https://developers.openai.com/codex/enterprise/workspace-model-availability)

### Advanced deployment

*   [Amazon Bedrock](https://developers.openai.com/codex/amazon-bedrock)
*   [GovCloud deployment](https://developers.openai.com/codex/enterprise/govcloud-configuration)
*   [Connect to a gateway](https://developers.openai.com/codex/enterprise/connect-to-a-gateway)
*   [Roll out a gateway](https://developers.openai.com/codex/enterprise/roll-out-a-gateway)

### ChatGPT EDU

*   [Education plans](https://developers.openai.com/codex/enterprise/education-plans)
*   [Higher education setup](https://developers.openai.com/codex/enterprise/higher-education-roles-and-permissions)

### ChatGPT Work

*   [Overview](https://developers.openai.com/codex/enterprise/chatgpt-work-overview)
*   [Cloud security](https://developers.openai.com/codex/enterprise/chatgpt-work-cloud-security)
*   [Local security](https://developers.openai.com/codex/enterprise/chatgpt-work-local-security)
*   [Usage and cost](https://developers.openai.com/codex/enterprise/chatgpt-work-usage-and-cost)
*   [Admin FAQ](https://developers.openai.com/codex/enterprise/work-admin-faq)

### Collaboration and sharing

*   [GPTs and sharing](https://developers.openai.com/codex/enterprise/gpts-and-sharing)

### Plugins and connections

*   [Plugin controls](https://developers.openai.com/codex/enterprise/apps-and-connectors)
*   [Import and sync plugins from GitHub](https://developers.openai.com/codex/enterprise/plugin-management)
*   [Skill controls](https://developers.openai.com/codex/enterprise/skills)
*   [Migrate custom GPTs to plugins](https://developers.openai.com/codex/migrate-custom-gpts)

### Usage and analytics

*   [Workspace analytics](https://developers.openai.com/codex/enterprise/workspace-analytics)
*   [Usage Insights](https://developers.openai.com/codex/enterprise/usage-insights)
*   [Analytics API](https://developers.openai.com/codex/enterprise/analytics-api)

### Security and compliance

*   [Governance](https://developers.openai.com/codex/enterprise/governance)
*   [Agent security](https://developers.openai.com/codex/enterprise/agent-security)
*   [Safety and security in dots](https://developers.openai.com/codex/enterprise/dots-security)
*   [Prisma AIRS](https://developers.openai.com/codex/enterprise/prisma-airs)
*   [HIPAA configuration](https://developers.openai.com/codex/hipaa-configuration)
*   [Compliance API and audit events](https://developers.openai.com/codex/enterprise/compliance-api)

*   [Explore use cases](https://developers.openai.com/codex/use-cases)
*   [Collections](https://developers.openai.com/codex/use-cases/collections)

*   [Home](https://developers.openai.com/codex/resources)
*   [Videos](https://developers.openai.com/codex/videos)
*   [Showcase](https://developers.openai.com/showcase)
*   [OpenAI Academy](https://openai.com/academy/)
*   [Online trainings](https://academy.openai.com/home/events)

### Community

*   [Codex Ambassadors](https://developers.openai.com/community/codex-ambassadors)
*   [Codex for Students](https://developers.openai.com/community/students)
*   [Codex for Open Source](https://developers.openai.com/community/codex-for-oss)
*   [Events](https://luma.com/codex-community?utm_source=oaidevs)

### Blog

*   [Company blog](https://openai.com/news/)
*   [Developer blog](https://developers.openai.com/blog)

*   [Explore use cases](https://developers.openai.com/codex/use-cases)
*   [Collections](https://developers.openai.com/codex/use-cases/collections)

*   [Home](https://developers.openai.com/codex/resources)
*   [Videos](https://developers.openai.com/codex/videos)
*   [Showcase](https://developers.openai.com/showcase)
*   [OpenAI Academy](https://openai.com/academy/)
*   [Online trainings](https://academy.openai.com/home/events)

### Community

*   [Codex Ambassadors](https://developers.openai.com/community/codex-ambassadors)
*   [Codex for Students](https://developers.openai.com/community/students)
*   [Codex for Open Source](https://developers.openai.com/community/codex-for-oss)
*   [Events](https://luma.com/codex-community?utm_source=oaidevs)

### Blog

*   [Company blog](https://openai.com/news/)
*   [Developer blog](https://developers.openai.com/blog)

[Showcase](https://developers.openai.com/showcase) Blog  Cookbook  Learn  Community 

Docs Showcase

*   [All posts](https://developers.openai.com/blog)

### Recent

*   [Designing failover across OpenAI model providers](https://developers.openai.com/blog/designing-failover-across-openai-model-providers)
*   [Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)
*   [Bringing my LED display to life with GPT-Live-1 and Codex](https://developers.openai.com/blog/bringing-my-led-display-to-life)
*   [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
*   [Architectural visualization with Astra](https://developers.openai.com/blog/architectural-visualization-with-astra)

### Topics

*   [General](https://developers.openai.com/blog/topic/general)
*   [API](https://developers.openai.com/blog/topic/api)
*   [Apps SDK](https://developers.openai.com/blog/topic/apps-sdk)
*   [Audio](https://developers.openai.com/blog/topic/audio)
*   [Codex](https://developers.openai.com/blog/topic/codex)
*   [Life sciences](https://developers.openai.com/blog/topic/life-sciences)

*   [Home](https://developers.openai.com/cookbook)

### Topics

*   [Sign-in with ChatGPT](https://developers.openai.com/cookbook/topic/sign-in-with-chatgpt)
*   [Agents](https://developers.openai.com/cookbook/topic/agents)
*   [Evals](https://developers.openai.com/cookbook/topic/evals)
*   [Multimodal](https://developers.openai.com/cookbook/topic/multimodal)
*   [Text](https://developers.openai.com/cookbook/topic/text)
*   [Guardrails](https://developers.openai.com/cookbook/topic/guardrails)
*   [Optimization](https://developers.openai.com/cookbook/topic/optimization)
*   [ChatGPT](https://developers.openai.com/cookbook/topic/chatgpt)
*   [Codex](https://developers.openai.com/cookbook/topic/codex)
*   [gpt-oss](https://developers.openai.com/cookbook/topic/gpt-oss)

### Contribute

*   [Cookbook on GitHub](https://github.com/openai/openai-cookbook)

*   [Home](https://developers.openai.com/learn)
*   [OpenAI Developers plugin](https://developers.openai.com/learn/developers-codex-plugin)
*   [Docs MCP](https://developers.openai.com/learn/docs-mcp)

### Categories

*   [Demo apps](https://developers.openai.com/learn/code)
*   [Videos](https://developers.openai.com/learn/videos)

### Topics

*   [Agents](https://developers.openai.com/learn/agents)
*   [Audio & Voice](https://developers.openai.com/learn/audio)
*   [Computer Use](https://developers.openai.com/learn/cua)
*   [Codex](https://developers.openai.com/learn/codex)
*   [Evals](https://developers.openai.com/learn/evals)
*   [gpt-oss](https://developers.openai.com/learn/gpt-oss)
*   [Fine-tuning](https://developers.openai.com/learn/fine-tuning)
*   [Image generation](https://developers.openai.com/learn/imagegen)
*   [Scaling](https://developers.openai.com/learn/scaling)
*   [Tools](https://developers.openai.com/learn/tools)
*   [Video generation](https://developers.openai.com/learn/videogen)

*   [Community](https://developers.openai.com/community)

### Programs

*   
[Codex Ambassadors](https://developers.openai.com/community/codex-ambassadors)
    *   [Meet the ambassadors](https://developers.openai.com/community/codex-ambassadors/directory)

*   [Codex for Students](https://developers.openai.com/community/students)
*   [Codex for Open Source](https://developers.openai.com/community/codex-for-oss)
*   [OpenAI for Startups](https://openai.com/business/why-openai/startups/)

### Spaces

*   [Events](https://luma.com/codex-community?utm_source=oaidevs)
*   [Developer Forum](https://community.openai.com/)
*   [Discord](https://discord.com/invite/openai)
*   [Reddit](https://www.reddit.com/r/OpenAI/)
*   [X](https://x.com/OpenAIDevs)

[API Dashboard](https://platform.openai.com/login)

[Try ChatGPT](https://chatgpt.com/)

*   [Model catalog](https://developers.openai.com/api/docs/models)

### Choose a model

*   [Pricing](https://developers.openai.com/api/docs/pricing)
*   [Model selection](https://developers.openai.com/api/docs/guides/model-selection)

### Text and code

*   [Text generation](https://developers.openai.com/api/docs/guides/text)
*   [Code generation](https://developers.openai.com/api/docs/guides/code-generation)
*   [Structured output](https://developers.openai.com/api/docs/guides/structured-outputs)

### Prompting

*   [Overview](https://developers.openai.com/api/docs/guides/prompting)
*   [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
*   [Citation formatting](https://developers.openai.com/api/docs/guides/citation-formatting)
*   [Migration guide](https://developers.openai.com/api/docs/guides/prompting/migrate-from-prompt-object)
*   [Prompt generation](https://developers.openai.com/api/docs/guides/prompt-generation)
*   [Frontend prompting](https://developers.openai.com/api/docs/guides/frontend-prompt)

### Reasoning

*   [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
*   [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)

### Images

*   
[Images and vision](https://developers.openai.com/api/docs/guides/images-vision)
    *   [Image input cost calculator](https://developers.openai.com/api/docs/guides/image-cost-calculator)

*   
[Image generation](https://developers.openai.com/api/docs/guides/image-generation)
    *   [Overview](https://developers.openai.com/api/docs/guides/image-generation)
    *   [Image prompting](https://developers.openai.com/api/docs/guides/image-prompting)

### Realtime and audio

*   [Audio and speech](https://developers.openai.com/api/docs/guides/audio)
*   [Getting started](https://developers.openai.com/api/docs/guides/realtime)
*   [Voice agents](https://developers.openai.com/api/docs/guides/voice-agents)

### Specialized models

*   [Embeddings](https://developers.openai.com/api/docs/guides/embeddings)
*   [Moderation](https://developers.openai.com/api/docs/guides/moderation)

Responses

Copy Page

# Structured model outputs

Copy Page

Ensure text responses from the model adhere to a JSON schema you define.

Responses

JSON is one of the most widely used formats in the world for applications to exchange data.

Structured Outputs is a feature that ensures the model will always generate responses that adhere to your supplied [JSON Schema](https://json-schema.org/overview/what-is-jsonschema), so you don’t need to worry about the model omitting a required key, or hallucinating an invalid enum value.

Some benefits of Structured Outputs include:

1.   **Reliable type-safety:** No need to validate or retry incorrectly formatted responses
2.   **Explicit refusals:** Safety-based model refusals are now programmatically detectable
3.   **Simpler prompting:** No need for strongly worded prompts to achieve consistent formatting

In addition to supporting JSON Schema in the REST API, the OpenAI libraries for [Python](https://github.com/openai/openai-python/blob/main/helpers.md#structured-outputs-parsing-helpers) and [JavaScript](https://github.com/openai/openai-node/blob/master/helpers.md#structured-outputs-parsing-helpers) also let you define object schemas using [`pydantic.BaseModel`](https://docs.pydantic.dev/latest/) and [`z.object`](https://zod.dev/) respectively. Below, you can see how to extract information from unstructured text that conforms to a schema defined in code.

The Ruby SDK supports schemas defined with Sorbet `T::Struct` and returns typed parsed results.

Getting a structured response

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25import OpenAI from "openai";
import { zodResponseFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const CalendarEvent = z.object({
  name: z.string(),
  date: z.string(),
  participants: z.array(z.string()),
});

const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    { role: "system", content: "Extract the event information." },
    {
      role: "user",
      content: "Alice and Bob are going to a science fair on Friday.",
    },
  ],
  response_format: zodResponseFormat(CalendarEvent, "event"),
});

const event = completion.choices[0].message.parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {
            "role": "user",
            "content": "Alice and Bob are going to a science fair on Friday.",
        },
    ],
    response_format=CalendarEvent,
)

event = completion.choices[0].message.parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"name":         map[string]any{"type": "string"},
			"date":         map[string]any{"type": "string"},
			"participants": map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
		},
		"required":             []string{"name", "date", "participants"},
		"additionalProperties": false,
	}

	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("Extract the event information."),
			openai.UserMessage("Alice and Bob are going to a science fair on Friday."),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "event", Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(completion.Choices[0].Message.Content)
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "name", Map.of("type", "string"),
            "date", Map.of("type", "string"),
            "participants", Map.of("type", "array", "items", Map.of("type", "string"))),
        "required",
        List.of("name", "date", "participants"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage("Extract the event information.")
        .addUserMessage("Alice and Bob are going to a science fair on Friday.")
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "event", "strict", true, "schema", schema))))
        .build();

client.chat().completions().create(params).choices().stream()
    .flatMap(choice -> choice.message().content().stream())
    .forEach(System.out::println);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "date": { "type": "string" },
        "participants": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["name", "date", "participants"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "event",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [
        new SystemChatMessage("Extract the event information."),
        new UserChatMessage(
            "Alice and Bob are going to a science fair on Friday."
        ),
    ],
    options
);

Console.WriteLine(completion.Content[0].Text);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34# gem install openai sorbet-runtime
require "openai"
require "openai/helpers/sorbet"

class CalendarEvent < T::Struct
  const :name, String
  const :date, String
  const :participants, T::Array[String]
end

client = OpenAI::Client.new
schema = OpenAI::StructuredOutput.from_sorbet(CalendarEvent)

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "Extract the event information."
    },
    {
      role: :user,
      content: "Alice and Bob are going to a science fair on Friday."
    }
  ],
  response_format: schema
)

choice = completion.choices.fetch(0)
raise "Completion ended with reason: #{choice.finish_reason}" unless choice.finish_reason.to_s == "stop"
raise "The model refused the request" if choice.message.refusal

event = T.cast(choice.message.parsed, CalendarEvent)
puts(event.name, event.date, event.participants.join(", "))
```

Getting a structured response

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const CalendarEvent = z.object({
  name: z.string(),
  date: z.string(),
  participants: z.array(z.string()),
});

const response = await openai.responses.parse({
  model: "gpt-6-astra",
  input: [
    { role: "system", content: "Extract the event information." },
    {
      role: "user",
      content: "Alice and Bob are going to a science fair on Friday.",
    },
  ],
  text: {
    format: zodTextFormat(CalendarEvent, "event"),
  },
});

const event = response.output_parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

response = client.responses.parse(
    model="gpt-6-astra",
    input=[
        {"role": "system", "content": "Extract the event information."},
        {
            "role": "user",
            "content": "Alice and Bob are going to a science fair on Friday.",
        },
    ],
    text_format=CalendarEvent,
)

event = response.output_parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"name":         map[string]any{"type": "string"},
			"date":         map[string]any{"type": "string"},
			"participants": map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
		},
		"required":             []string{"name", "date", "participants"},
		"additionalProperties": false,
	}

	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("Extract the event information.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("Alice and Bob are going to a science fair on Friday.")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "event", Schema: schema, Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(response.OutputText())
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "name", Map.of("type", "string"),
            "date", Map.of("type", "string"),
            "participants", Map.of("type", "array", "items", Map.of("type", "string"))),
        "required",
        List.of("name", "date", "participants"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content("Extract the event information.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("Alice and Bob are going to a science fair on Friday.")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("event")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "date": { "type": "string" },
        "participants": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["name", "date", "participants"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "event",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(
    ResponseItem.CreateSystemMessageItem("Extract the event information.")
);
options.InputItems.Add(
    ResponseItem.CreateUserMessageItem(
        "Alice and Bob are going to a science fair on Friday."
    )
);

ResponseResult response = await client.CreateResponseAsync(options);

Console.WriteLine(response.GetOutputText());
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36# gem install openai sorbet-runtime
require "openai"
require "openai/helpers/sorbet"

class CalendarEvent < T::Struct
  const :name, String
  const :date, String
  const :participants, T::Array[String]
end

client = OpenAI::Client.new
schema = OpenAI::StructuredOutput.from_sorbet(CalendarEvent)

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "Extract the event information."
    },
    {
      role: :user,
      content: "Alice and Bob are going to a science fair on Friday."
    }
  ],
  text: schema
)

raise "Response ended with status: #{response.status}" unless response.status == OpenAI::Responses::ResponseStatus::COMPLETED

message = response.output.grep(OpenAI::Responses::ResponseOutputMessage).fetch(0)
output_text = message.content.grep(OpenAI::Responses::ResponseOutputText).first
raise "No structured output returned (the model may have refused)" unless output_text

event = T.cast(output_text.parsed, CalendarEvent)
puts(event.name, event.date, event.participants.join(", "))
```

### Supported models

Structured Outputs is available in our [latest large language models](https://developers.openai.com/api/docs/models), starting with GPT-4o. For new projects, start with [`gpt-6-astra`](https://developers.openai.com/api/docs/models/gpt-6-astra). Older models like `gpt-4-turbo` and earlier may use [JSON mode](https://developers.openai.com/api/docs/guides/structured-outputs#json-mode) instead.

## When to use Structured Outputs via function calling vs via response_format

## When to use Structured Outputs via function calling vs via text.format

Structured Outputs is available in two forms in the OpenAI API:

1.   When using [function calling](https://developers.openai.com/api/docs/guides/function-calling)
2.   When using a `json_schema` response format

Function calling is useful when you are building an application that bridges the models and functionality of your application.

For example, you can give the model access to functions that query a database in order to build an AI assistant that can help users with their orders, or functions that can interact with the UI.

Conversely, Structured Outputs via `response_format` are more suitable when you want to indicate a structured schema for use when the model responds to the user, rather than when the model calls a tool.

For example, if you are building a math tutoring application, you might want the assistant to respond to your user using a specific JSON Schema so that you can generate a UI that displays different parts of the model’s output in distinct ways.

In practice:

*   If you are connecting the model to tools, functions, data, etc. in your system, then you should use function calling - If you want to structure the model’s output when it responds to the user, then you should use a structured `response_format`

*   If you are connecting the model to tools, functions, data, etc. in your system, then you should use function calling - If you want to structure the model’s output when it responds to the user, then you should use a structured `text.format`

The remainder of this guide will focus on non-function calling use cases in the Chat Completions API. To learn more about how to use Structured Outputs with function calling, check out the

[Function Calling](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)
guide.

The remainder of this guide will focus on non-function calling use cases in the Responses API. To learn more about how to use Structured Outputs with function calling, check out the

[Function Calling](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)
guide.

### Structured Outputs vs JSON mode

Structured Outputs is the evolution of [JSON mode](https://developers.openai.com/api/docs/guides/structured-outputs#json-mode). While both ensure valid JSON is produced, only Structured Outputs ensure schema adherence. Both Structured Outputs and JSON mode are supported in the Responses API, Chat Completions API, Assistants API, Fine-tuning API and Batch API.

We recommend always using Structured Outputs instead of JSON mode when possible.

However, Structured Outputs with `response_format: {type: "json_schema", ...}` is only supported with the `gpt-4o-mini`, `gpt-4o-mini-2024-07-18`, and `gpt-4o-2024-08-06` model snapshots and later.

|  | Structured Outputs | JSON Mode |
| --- | --- | --- |
| **Outputs valid JSON** | Yes | Yes |
| **Adheres to schema** | Yes (see [supported schemas](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas)) | No |
| **Compatible models** | `gpt-4o-mini`, `gpt-4o-2024-08-06`, and later | `gpt-3.5-turbo`, `gpt-4-*`, `gpt-4o-*`, and compatible GPT-5 models |
| **Enabling** | `response_format: { type: "json_schema", json_schema: {"strict": true, "schema": ...} }` | `response_format: { type: "json_object" }` |

|  | Structured Outputs | JSON Mode |
| --- | --- | --- |
| **Outputs valid JSON** | Yes | Yes |
| **Adheres to schema** | Yes (see [supported schemas](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas)) | No |
| **Compatible models** | `gpt-4o-mini`, `gpt-4o-2024-08-06`, and later | `gpt-3.5-turbo`, `gpt-4-*`, `gpt-4o-*`, and compatible GPT-5 models |
| **Enabling** | `text: { format: { type: "json_schema", "strict": true, "schema": ... } }` | `text: { format: { type: "json_object" } }` |

## Examples

Chain of thought Structured data extraction UI generation Moderation

Chain of thought

### Chain of thought

You can ask the model to output an answer in a structured, step-by-step way, to guide the user through the solution.

Structured Outputs for chain-of-thought math tutoring

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30import OpenAI from "openai";
import { z } from "zod";
import { zodResponseFormat } from "openai/helpers/zod";

const openai = new OpenAI();

const Step = z.object({
  explanation: z.string(),
  output: z.string(),
});

const MathReasoning = z.object({
  steps: z.array(Step),
  final_answer: z.string(),
});

const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  response_format: zodResponseFormat(MathReasoning, "math_reasoning"),
});

const math_reasoning = completion.choices[0].message.parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format=MathReasoning,
)

math_reasoning = completion.choices[0].message.parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	step := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"explanation": map[string]any{"type": "string"},
			"output":      map[string]any{"type": "string"},
		},
		"required":             []string{"explanation", "output"},
		"additionalProperties": false,
	}
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": step},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}

	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_reasoning", Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(completion.Choices[0].Message.Content)
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps",
                Map.of(
                    "type",
                    "array",
                    "items",
                    Map.of(
                        "type",
                        "object",
                        "properties",
                        Map.of(
                            "explanation", Map.of("type", "string"),
                            "output", Map.of("type", "string")),
                        "required",
                        List.of("explanation", "output"),
                        "additionalProperties",
                        false)),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_reasoning", "strict", true, "schema", schema))))
        .build();

client.chat().completions().create(params).choices().stream()
    .flatMap(choice -> choice.message().content().stream())
    .forEach(System.out::println);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46using System.Text.Json;
using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

using JsonDocument parsed = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_reasoning",
      strict: true,
      schema: math_schema
    }
  }
)

puts(completion.choices.fetch(0).message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "math_reasoning",
        "schema": {
          "type": "object",
          "properties": {
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "explanation": { "type": "string" },
                  "output": { "type": "string" }
                },
                "required": ["explanation", "output"],
                "additionalProperties": false
              }
            },
            "final_answer": { "type": "string" }
          },
          "required": ["steps", "final_answer"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

Structured Outputs for chain-of-thought math tutoring

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const Step = z.object({
  explanation: z.string(),
  output: z.string(),
});

const MathReasoning = z.object({
  steps: z.array(Step),
  final_answer: z.string(),
});

const response = await openai.responses.parse({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  text: {
    format: zodTextFormat(MathReasoning, "math_reasoning"),
  },
});

const math_reasoning = response.output_parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

response = client.responses.parse(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    text_format=MathReasoning,
)

math_reasoning = response.output_parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	step := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"explanation": map[string]any{"type": "string"},
			"output":      map[string]any{"type": "string"},
		},
		"required":             []string{"explanation", "output"},
		"additionalProperties": false,
	}
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": step},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}

	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful math tutor. Guide the user through the solution step by step.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("how can I solve 8x + 7 = -23")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "math_reasoning", Schema: schema, Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(response.OutputText())
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps",
                Map.of(
                    "type",
                    "array",
                    "items",
                    Map.of(
                        "type",
                        "object",
                        "properties",
                        Map.of(
                            "explanation", Map.of("type", "string"),
                            "output", Map.of("type", "string")),
                        "required",
                        List.of("explanation", "output"),
                        "additionalProperties",
                        false)),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are a helpful math tutor. Guide the user through the solution step by step.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How can I solve 8x + 7 = -23?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("math_reasoning")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49using System.Text.Json;
using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "math_response",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful math tutor. Guide the user through the solution step by step."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How can I solve 8x + 7 = -23?"));

ResponseResult response = await client.CreateResponseAsync(options);
using JsonDocument parsed = JsonDocument.Parse(response.GetOutputText());
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "math_reasoning",
      strict: true,
      schema: math_schema
    }
  }
)

puts(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "math_reasoning",
        "schema": {
          "type": "object",
          "properties": {
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "explanation": { "type": "string" },
                  "output": { "type": "string" }
                },
                "required": ["explanation", "output"],
                "additionalProperties": false
              }
            },
            "final_answer": { "type": "string" }
          },
          "required": ["steps", "final_answer"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

#### Example response

```
{
  "steps": [
    {
      "explanation": "Start with the equation 8x + 7 = -23.",
      "output": "8x + 7 = -23"
    },
    {
      "explanation": "Subtract 7 from both sides to isolate the term with the variable.",
      "output": "8x = -23 - 7"
    },
    {
      "explanation": "Simplify the right side of the equation.",
      "output": "8x = -30"
    },
    {
      "explanation": "Divide both sides by 8 to solve for x.",
      "output": "x = -30 / 8"
    },
    {
      "explanation": "Simplify the fraction.",
      "output": "x = -15 / 4"
    }
  ],
  "final_answer": "x = -15 / 4"
}
```

Structured data extraction

### Structured data extraction

You can define structured fields to extract from unstructured input data, such as research papers.

Extracting data from research papers using Structured Outputs

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30import OpenAI from "openai";
import { z } from "zod";
import { zodResponseFormat } from "openai/helpers/zod";

const openai = new OpenAI();

const ResearchPaperExtraction = z.object({
  title: z.string(),
  authors: z.array(z.string()),
  abstract: z.string(),
  keywords: z.array(z.string()),
});

const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure.",
    },
    { role: "user", content: "..." },
  ],
  response_format: zodResponseFormat(
    ResearchPaperExtraction,
    "research_paper_extraction"
  ),
});

const research_paper = completion.choices[0].message.parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class ResearchPaperExtraction(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]

completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure.",
        },
        {
            "role": "user",
            "content": (
                "Attention Is All You Need by Ashish Vaswani, Noam Shazeer, "
                "Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, "
                "Łukasz Kaiser, and Illia Polosukhin. We propose the "
                "Transformer, a sequence transduction architecture based "
                "entirely on attention. Keywords: transformers, attention, "
                "sequence transduction."
            ),
        },
    ],
    response_format=ResearchPaperExtraction,
)

research_paper = completion.choices[0].message.parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

const researchPaperText = "Attention Is All You Need by Ashish Vaswani, Noam Shazeer, " +
	"Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, " +
	"Łukasz Kaiser, and Illia Polosukhin. We propose the Transformer, " +
	"a sequence transduction architecture based entirely on attention. " +
	"Keywords: transformers, attention, sequence transduction."

func main() {
	client := openai.NewClient()
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"title":    map[string]any{"type": "string"},
			"authors":  map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
			"abstract": map[string]any{"type": "string"},
			"keywords": map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
		},
		"required":             []string{"title", "authors", "abstract", "keywords"},
		"additionalProperties": false,
	}

	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure."),
			openai.UserMessage(researchPaperText),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "research_paper_extraction", Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(completion.Choices[0].Message.Content)
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "title", Map.of("type", "string"),
            "authors", Map.of("type", "array", "items", Map.of("type", "string")),
            "abstract", Map.of("type", "string"),
            "keywords", Map.of("type", "array", "items", Map.of("type", "string"))),
        "required",
        List.of("title", "authors", "abstract", "keywords"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are an expert at structured data extraction. You will be given unstructured"
                + " text from a research paper and should convert it into the given structure.")
        .addUserMessage(
            "Attention Is All You Need by Ashish Vaswani, Noam Shazeer, Niki Parmar,"
                + " Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and"
                + " Illia Polosukhin."
                + " We propose the Transformer, a sequence transduction architecture based"
                + " entirely on attention. Keywords: transformers, attention, sequence"
                + " transduction.")
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of(
                        "name",
                        "research_paper_extraction",
                        "strict",
                        true,
                        "schema",
                        schema))))
        .build();

client.chat().completions().create(params).choices().stream()
    .flatMap(choice -> choice.message().content().stream())
    .forEach(System.out::println);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49using System.Text.Json;
using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "authors": { "type": "array", "items": { "type": "string" } },
        "abstract": { "type": "string" },
        "keywords": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["title", "authors", "abstract", "keywords"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "research_paper",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [
        new SystemChatMessage("Extract the title, authors, abstract, and keywords from the research paper."),
        new UserChatMessage(
            """
            Attention Is All You Need by Ashish Vaswani, Noam Shazeer,
            Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez,
            Łukasz Kaiser, and Illia Polosukhin. We propose the
            Transformer, a sequence transduction architecture based
            entirely on attention. Keywords: transformers, attention,
            sequence transduction.
            """
        ),
    ],
    options
);

using JsonDocument parsed = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51require "openai"

client = OpenAI::Client.new
research_paper = <<~TEXT
  Attention Is All You Need by Ashish Vaswani, Noam Shazeer, Niki Parmar,
  Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia
  Polosukhin. We propose the Transformer, a sequence transduction architecture
  based entirely on attention. Keywords: transformers, attention, sequence
  transduction.
TEXT
paper_schema = {
  type: :object,
  properties: {
    title: { type: :string },
    authors: {
      type: :array,
      items: { type: :string }
    },
    abstract: { type: :string },
    keywords: {
      type: :array,
      items: { type: :string }
    }
  },
  required: %w[title authors abstract keywords],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "Extract structured data from the supplied research paper text."
    },
    {
      role: :user,
      content: research_paper
    }
  ],
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "research_paper_extraction",
      strict: true,
      schema: paper_schema
    }
  }
)

puts(completion.choices.fetch(0).message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "messages": [
      {
        "role": "system",
        "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure."
      },
      {
        "role": "user",
        "content": "..."
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "research_paper_extraction",
        "schema": {
          "type": "object",
          "properties": {
            "title": { "type": "string" },
            "authors": {
              "type": "array",
              "items": { "type": "string" }
            },
            "abstract": { "type": "string" },
            "keywords": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["title", "authors", "abstract", "keywords"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

Extracting data from research papers using Structured Outputs

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const ResearchPaperExtraction = z.object({
  title: z.string(),
  authors: z.array(z.string()),
  abstract: z.string(),
  keywords: z.array(z.string()),
});

const response = await openai.responses.parse({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content:
        "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure.",
    },
    { role: "user", content: "..." },
  ],
  text: {
    format: zodTextFormat(ResearchPaperExtraction, "research_paper_extraction"),
  },
});

const research_paper = response.output_parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class ResearchPaperExtraction(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]

response = client.responses.parse(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure.",
        },
        {
            "role": "user",
            "content": (
                "Attention Is All You Need by Ashish Vaswani, Noam Shazeer, "
                "Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, "
                "Łukasz Kaiser, and Illia Polosukhin. We propose the "
                "Transformer, a sequence transduction architecture based "
                "entirely on attention. Keywords: transformers, attention, "
                "sequence transduction."
            ),
        },
    ],
    text_format=ResearchPaperExtraction,
)

research_paper = response.output_parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

const researchPaperText = "Attention Is All You Need by Ashish Vaswani, Noam Shazeer, " +
	"Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, " +
	"Łukasz Kaiser, and Illia Polosukhin. We propose the Transformer, " +
	"a sequence transduction architecture based entirely on attention. " +
	"Keywords: transformers, attention, sequence transduction."

func main() {
	client := openai.NewClient()
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"title":    map[string]any{"type": "string"},
			"authors":  map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
			"abstract": map[string]any{"type": "string"},
			"keywords": map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
		},
		"required":             []string{"title", "authors", "abstract", "keywords"},
		"additionalProperties": false,
	}

	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText(researchPaperText)},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "research_paper_extraction", Schema: schema, Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(response.OutputText())
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "title", Map.of("type", "string"),
            "authors", Map.of("type", "array", "items", Map.of("type", "string")),
            "abstract", Map.of("type", "string"),
            "keywords", Map.of("type", "array", "items", Map.of("type", "string"))),
        "required",
        List.of("title", "authors", "abstract", "keywords"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are an expert at structured data extraction. You will be given"
                                + " unstructured text from a research paper and should convert"
                                + " it into the given structure.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content(
                            "Attention Is All You Need by Ashish Vaswani, Noam Shazeer,"
                                + " Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez,"
                                + " Łukasz Kaiser, and Illia Polosukhin. We propose the"
                                + " Transformer, a"
                                + " sequence transduction architecture based entirely on"
                                + " attention. Keywords: transformers, attention, sequence"
                                + " transduction.")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("research_paper_extraction")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51using System.Text.Json;
using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "authors": { "type": "array", "items": { "type": "string" } },
        "abstract": { "type": "string" },
        "keywords": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["title", "authors", "abstract", "keywords"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "research_paper",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("Extract the title, authors, abstract, and keywords from the research paper."));
options.InputItems.Add(
    ResponseItem.CreateUserMessageItem(
        """
        Attention Is All You Need by Ashish Vaswani, Noam Shazeer,
        Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez,
        Łukasz Kaiser, and Illia Polosukhin. We propose the
        Transformer, a sequence transduction architecture based
        entirely on attention. Keywords: transformers, attention,
        sequence transduction.
        """
    )
);

ResponseResult response = await client.CreateResponseAsync(options);
using JsonDocument parsed = JsonDocument.Parse(response.GetOutputText());
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51require "openai"

client = OpenAI::Client.new
research_paper = <<~TEXT
  Attention Is All You Need by Ashish Vaswani, Noam Shazeer, Niki Parmar,
  Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia
  Polosukhin. We propose the Transformer, a sequence transduction architecture
  based entirely on attention. Keywords: transformers, attention, sequence
  transduction.
TEXT
paper_schema = {
  type: :object,
  properties: {
    title: { type: :string },
    authors: {
      type: :array,
      items: { type: :string }
    },
    abstract: { type: :string },
    keywords: {
      type: :array,
      items: { type: :string }
    }
  },
  required: %w[title authors abstract keywords],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "Extract structured data from the supplied research paper text."
    },
    {
      role: :user,
      content: research_paper
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "research_paper_extraction",
      strict: true,
      schema: paper_schema
    }
  }
)

puts(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure."
      },
      {
        "role": "user",
        "content": "..."
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "research_paper_extraction",
        "schema": {
          "type": "object",
          "properties": {
            "title": { "type": "string" },
            "authors": {
              "type": "array",
              "items": { "type": "string" }
            },
            "abstract": { "type": "string" },
            "keywords": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["title", "authors", "abstract", "keywords"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

#### Example response

```
{
  "title": "Application of Quantum Algorithms in Interstellar Navigation: A New Frontier",
  "authors": ["Dr. Stella Voyager", "Dr. Nova Star", "Dr. Lyra Hunter"],
  "abstract": "This paper investigates the utilization of quantum algorithms to improve interstellar navigation systems. By leveraging quantum superposition and entanglement, our proposed navigation system can calculate optimal travel paths through space-time anomalies more efficiently than classical methods. Experimental simulations suggest a significant reduction in travel time and fuel consumption for interstellar missions.",
  "keywords": [
    "Quantum algorithms",
    "interstellar navigation",
    "space-time anomalies",
    "quantum superposition",
    "quantum entanglement",
    "space travel"
  ]
}
```

UI generation

### UI Generation

You can generate valid HTML by representing it as recursive data structures with constraints, like enums.

Generating HTML using Structured Outputs

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33import OpenAI from "openai";
import { z } from "zod";
import { zodResponseFormat } from "openai/helpers/zod";

const openai = new OpenAI();

const UI = z.lazy(() =>
  z.object({
    type: z.enum(["div", "button", "header", "section", "field", "form"]),
    label: z.string(),
    children: z.array(UI),
    attributes: z.array(
      z.object({
        name: z.string(),
        value: z.string(),
      })
    ),
  })
);

const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content: "You are a UI generator AI. Convert the user input into a UI.",
    },
    { role: "user", content: "Make a User Profile Form" },
  ],
  response_format: zodResponseFormat(UI, "ui"),
});

const ui = completion.choices[0].message.parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49from enum import Enum
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class UIType(str, Enum):
    div = "div"
    button = "button"
    header = "header"
    section = "section"
    field = "field"
    form = "form"

class Attribute(BaseModel):
    name: str
    value: str

class UI(BaseModel):
    type: UIType
    label: str
    children: list["UI"]
    attributes: list[Attribute]

UI.model_rebuild()  # This is required to enable recursive types

class Response(BaseModel):
    ui: UI

completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are a UI generator AI. Convert the user input into a UI.",
        },
        {"role": "user", "content": "Make a User Profile Form"},
    ],
    response_format=Response,
)

ui = completion.choices[0].message.parsed
print(ui)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"type":       map[string]any{"type": "string", "enum": []string{"div", "button", "header", "section", "field", "form"}},
			"label":      map[string]any{"type": "string"},
			"children":   map[string]any{"type": "array", "items": map[string]any{"$ref": "#"}},
			"attributes": map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"name": map[string]any{"type": "string"}, "value": map[string]any{"type": "string"}}, "required": []string{"name", "value"}, "additionalProperties": false}},
		},
		"required":             []string{"type", "label", "children", "attributes"},
		"additionalProperties": false,
	}

	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a UI generator AI. Convert the user input into a UI."),
			openai.UserMessage("Make a User Profile Form"),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "ui", Description: openai.String("Dynamically generated UI"), Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(completion.Choices[0].Message.Content)
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

Map<String, Object> attributeProperties = new LinkedHashMap<>();
attributeProperties.put("name", Map.of("type", "string"));
attributeProperties.put("value", Map.of("type", "string"));

// Structured Outputs preserves the order of the schema's properties.
Map<String, Object> properties = new LinkedHashMap<>();
properties.put(
    "type",
    Map.of(
        "type",
        "string",
        "enum",
        List.of("div", "button", "header", "section", "field", "form")));
properties.put("label", Map.of("type", "string"));
properties.put("children", Map.of("type", "array", "items", Map.of("$ref", "#")));
properties.put(
    "attributes",
    Map.of(
        "type",
        "array",
        "items",
        Map.of(
            "type",
            "object",
            "properties",
            attributeProperties,
            "required",
            List.of("name", "value"),
            "additionalProperties",
            false)));

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        properties,
        "required",
        List.of("type", "label", "children", "attributes"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .maxCompletionTokens(4096)
        .addSystemMessage("Convert the user request into a UI definition.")
        .addUserMessage("Make a user profile form.")
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of(
                        "name",
                        "ui",
                        "description",
                        "A dynamically generated UI",
                        "strict",
                        true,
                        "schema",
                        schema))))
        .build();

var completion = client.chat().completions().create(params);
if (completion.choices().size() != 1) {
  throw new IllegalStateException("UI generation did not complete.");
}
var choice = completion.choices().get(0);
if (!choice.finishReason().equals(ChatCompletion.Choice.FinishReason.STOP)
    || choice.message().refusal().isPresent()
    || choice.message().content().filter(text -> !text.isBlank()).isEmpty()) {
  throw new IllegalStateException("UI generation did not complete.");
}
System.out.println(choice.message().content().orElseThrow());
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67using System.Text.Json;
using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "ui": { "$ref": "#/$defs/component" }
      },
      "required": ["ui"],
      "additionalProperties": false,
      "$defs": {
        "component": {
          "type": "object",
          "properties": {
            "type": { "type": "string", "enum": ["div", "button", "header", "section", "field", "form"] },
            "label": { "type": "string" },
            "attributes": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": { "name": { "type": "string" }, "value": { "type": "string" } },
                "required": ["name", "value"],
                "additionalProperties": false
              }
            },
            "children": { "type": "array", "items": { "$ref": "#/$defs/component" } }
          },
          "required": ["type", "label", "children", "attributes"],
          "additionalProperties": false
        }
      }
    }
    """
);
ChatCompletionOptions options = new()
{
    MaxOutputTokenCount = 4096,
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "ui",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [
        new SystemChatMessage("You are a UI generator. Convert the user request into a component tree."),
        new UserChatMessage(
            "Make a small user profile form with exactly three direct children: " +
            "a Name field, an Email field, and a Save button. Give each child no children. " +
            "Use short labels and at most two short attributes per component."
        ),
    ],
    options
);

if (completion.FinishReason != ChatFinishReason.Stop || !string.IsNullOrEmpty(completion.Refusal) ||
    completion.Content.Count != 1 || string.IsNullOrWhiteSpace(completion.Content[0].Text))
    throw new InvalidOperationException("UI generation did not complete.");

using JsonDocument parsed = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56require "openai"

client = OpenAI::Client.new
ui_schema = {
  type: :object,
  properties: {
    type: {
      type: :string,
      enum: %w[div button header section field form]
    },
    label: { type: :string },
    children: {
      type: :array,
      items: { "$ref" => "#" }
    },
    attributes: {
      type: :array,
      items: {
        type: :object,
        properties: {
          name: { type: :string },
          value: { type: :string }
        },
        required: %w[name value],
        additionalProperties: false
      }
    }
  },
  required: %w[type label children attributes],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "Convert the user request into a UI definition."
    },
    {
      role: :user,
      content: "Make a user profile form."
    }
  ],
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "ui",
      description: "A dynamically generated UI",
      strict: true,
      schema: ui_schema
    }
  }
)

puts(completion.choices.fetch(0).message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "messages": [
      {
        "role": "system",
        "content": "You are a UI generator AI. Convert the user input into a UI."
      },
      {
        "role": "user",
        "content": "Make a User Profile Form"
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "ui",
        "description": "Dynamically generated UI",
        "schema": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "description": "The type of the UI component",
              "enum": ["div", "button", "header", "section", "field", "form"]
            },
            "label": {
              "type": "string",
              "description": "The label of the UI component, used for buttons or form fields"
            },
            "children": {
              "type": "array",
              "description": "Nested UI components",
              "items": {"$ref": "#"}
            },
            "attributes": {
              "type": "array",
              "description": "Arbitrary attributes for the UI component, suitable for any element",
              "items": {
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string",
                    "description": "The name of the attribute, for example onClick or className"
                  },
                  "value": {
                    "type": "string",
                    "description": "The value of the attribute"
                  }
                },
                "required": ["name", "value"],
                "additionalProperties": false
              }
            }
          },
          "required": ["type", "label", "children", "attributes"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

Generating HTML using Structured Outputs

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const UI = z.lazy(() =>
  z.object({
    type: z.enum(["div", "button", "header", "section", "field", "form"]),
    label: z.string(),
    children: z.array(UI),
    attributes: z.array(
      z.object({
        name: z.string(),
        value: z.string(),
      })
    ),
  })
);

const response = await openai.responses.parse({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content: "You are a UI generator AI. Convert the user input into a UI.",
    },
    {
      role: "user",
      content: "Make a User Profile Form",
    },
  ],
  text: {
    format: zodTextFormat(UI, "ui"),
  },
});

const ui = response.output_parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49from enum import Enum

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class UIType(str, Enum):
    div = "div"
    button = "button"
    header = "header"
    section = "section"
    field = "field"
    form = "form"

class Attribute(BaseModel):
    name: str
    value: str

class UI(BaseModel):
    type: UIType
    label: str
    children: list["UI"]
    attributes: list[Attribute]

UI.model_rebuild()  # This is required to enable recursive types

class Response(BaseModel):
    ui: UI

response = client.responses.parse(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "You are a UI generator AI. Convert the user input into a UI.",
        },
        {"role": "user", "content": "Make a User Profile Form"},
    ],
    text_format=Response,
)

ui = response.output_parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	schema := map[string]any{
		"type": "object",
		"properties": map[string]any{
			"type":       map[string]any{"type": "string", "enum": []string{"div", "button", "header", "section", "field", "form"}},
			"label":      map[string]any{"type": "string"},
			"children":   map[string]any{"type": "array", "items": map[string]any{"$ref": "#"}},
			"attributes": map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"name": map[string]any{"type": "string"}, "value": map[string]any{"type": "string"}}, "required": []string{"name", "value"}, "additionalProperties": false}},
		},
		"required":             []string{"type", "label", "children", "attributes"},
		"additionalProperties": false,
	}

	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a UI generator AI. Convert the user input into a UI.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("Make a User Profile Form")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "ui", Description: openai.String("Dynamically generated UI"), Schema: schema, Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}

	fmt.Println(response.OutputText())
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

Map<String, Object> attributeProperties = new LinkedHashMap<>();
attributeProperties.put("name", Map.of("type", "string"));
attributeProperties.put("value", Map.of("type", "string"));

// Structured Outputs preserves the order of the schema's properties.
Map<String, Object> properties = new LinkedHashMap<>();
properties.put(
    "type",
    Map.of(
        "type",
        "string",
        "enum",
        List.of("div", "button", "header", "section", "field", "form")));
properties.put("label", Map.of("type", "string"));
properties.put("children", Map.of("type", "array", "items", Map.of("$ref", "#")));
properties.put(
    "attributes",
    Map.of(
        "type",
        "array",
        "items",
        Map.of(
            "type",
            "object",
            "properties",
            attributeProperties,
            "required",
            List.of("name", "value"),
            "additionalProperties",
            false)));

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content("Convert the user request into a UI definition.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("Make a user profile form.")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("ui")
                        .description("A dynamically generated UI")
                        .strict(true)
                        .schema(
                            ResponseFormatTextJsonSchemaConfig.Schema.builder()
                                .putAdditionalProperty("type", JsonValue.from("object"))
                                .putAdditionalProperty("properties", JsonValue.from(properties))
                                .putAdditionalProperty(
                                    "required",
                                    JsonValue.from(
                                        List.of("type", "label", "children", "attributes")))
                                .putAdditionalProperty(
                                    "additionalProperties", JsonValue.from(false))
                                .build())
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71using System.Text.Json;
using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "ui": { "$ref": "#/$defs/component" }
      },
      "required": ["ui"],
      "additionalProperties": false,
      "$defs": {
        "component": {
          "type": "object",
          "properties": {
            "type": { "type": "string", "enum": ["div", "button", "header", "section", "field", "form"] },
            "label": { "type": "string" },
            "attributes": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": { "name": { "type": "string" }, "value": { "type": "string" } },
                "required": ["name", "value"],
                "additionalProperties": false
              }
            },
            "children": { "type": "array", "items": { "$ref": "#/$defs/component" } }
          },
          "required": ["type", "label", "children", "attributes"],
          "additionalProperties": false
        }
      }
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    MaxOutputTokenCount = 4096,
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "ui",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a UI generator. Convert the user request into a component tree."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem(
    "Make a small user profile form with exactly three direct children: " +
    "a Name field, an Email field, and a Save button. Give each child no children. " +
    "Use short labels and at most two short attributes per component."
));

ResponseResult response = await client.CreateResponseAsync(options);
string text = response.GetOutputText();
bool refused = response.OutputItems.OfType<MessageResponseItem>()
    .SelectMany(message => message.Content)
    .Any(part => part.Kind == ResponseContentPartKind.Refusal);
if (response.Status != ResponseStatus.Completed || refused || string.IsNullOrWhiteSpace(text))
{
    throw new InvalidOperationException("UI generation did not complete.");
}
using JsonDocument parsed = JsonDocument.Parse(text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56require "openai"

client = OpenAI::Client.new
ui_schema = {
  type: :object,
  properties: {
    type: {
      type: :string,
      enum: %w[div button header section field form]
    },
    label: { type: :string },
    children: {
      type: :array,
      items: { "$ref" => "#" }
    },
    attributes: {
      type: :array,
      items: {
        type: :object,
        properties: {
          name: { type: :string },
          value: { type: :string }
        },
        required: %w[name value],
        additionalProperties: false
      }
    }
  },
  required: %w[type label children attributes],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "Convert the user request into a UI definition."
    },
    {
      role: :user,
      content: "Make a user profile form."
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "ui",
      description: "A dynamically generated UI",
      strict: true,
      schema: ui_schema
    }
  }
)

puts(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "You are a UI generator AI. Convert the user input into a UI."
      },
      {
        "role": "user",
        "content": "Make a User Profile Form"
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "ui",
        "description": "Dynamically generated UI",
        "schema": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "description": "The type of the UI component",
              "enum": ["div", "button", "header", "section", "field", "form"]
            },
            "label": {
              "type": "string",
              "description": "The label of the UI component, used for buttons or form fields"
            },
            "children": {
              "type": "array",
              "description": "Nested UI components",
              "items": {"$ref": "#"}
            },
            "attributes": {
              "type": "array",
              "description": "Arbitrary attributes for the UI component, suitable for any element",
              "items": {
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string",
                    "description": "The name of the attribute, for example onClick or className"
                  },
                  "value": {
                    "type": "string",
                    "description": "The value of the attribute"
                  }
                },
                "required": ["name", "value"],
                "additionalProperties": false
              }
            }
          },
          "required": ["type", "label", "children", "attributes"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

#### Example response

```
{
  "type": "form",
  "label": "User Profile Form",
  "children": [
    {
      "type": "div",
      "label": "",
      "children": [
        {
          "type": "field",
          "label": "First Name",
          "children": [],
          "attributes": [
            {
              "name": "type",
              "value": "text"
            },
            {
              "name": "name",
              "value": "firstName"
            },
            {
              "name": "placeholder",
              "value": "Enter your first name"
            }
          ]
        },
        {
          "type": "field",
          "label": "Last Name",
          "children": [],
          "attributes": [
            {
              "name": "type",
              "value": "text"
            },
            {
              "name": "name",
              "value": "lastName"
            },
            {
              "name": "placeholder",
              "value": "Enter your last name"
            }
          ]
        }
      ],
      "attributes": []
    },
    {
      "type": "button",
      "label": "Submit",
      "children": [],
      "attributes": [
        {
          "name": "type",
          "value": "submit"
        }
      ]
    }
  ],
  "attributes": [
    {
      "name": "method",
      "value": "post"
    },
    {
      "name": "action",
      "value": "/submit-profile"
    }
  ]
}
```

Moderation

### Moderation

You can classify inputs on multiple categories, which is a common way of doing moderation.

Moderation using Structured Outputs

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26import OpenAI from "openai";
import { z } from "zod";
import { zodResponseFormat } from "openai/helpers/zod";

const openai = new OpenAI();

const ContentCompliance = z.object({
  is_violating: z.boolean(),
  category: z.enum(["violence", "sexual", "self_harm"]).nullable(),
  explanation_if_violating: z.string().nullable(),
});

const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "Determine if the user input violates specific guidelines and explain if they do.",
    },
    { role: "user", content: "How do I prepare for a job interview?" },
  ],
  response_format: zodResponseFormat(ContentCompliance, "content_compliance"),
});

const compliance = completion.choices[0].message.parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32from enum import Enum
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class Category(str, Enum):
    violence = "violence"
    sexual = "sexual"
    self_harm = "self_harm"

class ContentCompliance(BaseModel):
    is_violating: bool
    category: Category | None
    explanation_if_violating: str | None

completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "Determine if the user input violates specific guidelines and explain if they do.",
        },
        {"role": "user", "content": "How do I prepare for a job interview?"},
    ],
    response_format=ContentCompliance,
)

compliance = completion.choices[0].message.parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	schema := contentComplianceSchema()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("Determine if the user input violates specific guidelines and explain if they do."),
			openai.UserMessage("How do I prepare for a job interview?"),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "content_compliance", Description: openai.String("Determines if content is violating specific moderation rules"), Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(completion.Choices[0].Message.Content)
}

func contentComplianceSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"is_violating":             map[string]any{"type": "boolean", "description": "Indicates if the content is violating guidelines"},
			"category":                 map[string]any{"type": []string{"string", "null"}, "description": "Type of violation, if the content is violating guidelines. Null otherwise.", "enum": []any{"violence", "sexual", "self_harm", nil}},
			"explanation_if_violating": map[string]any{"type": []string{"string", "null"}, "description": "Explanation of why the content is violating"},
		},
		"required":             []string{"is_violating", "category", "explanation_if_violating"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "is_violating",
                Map.of(
                    "type", "boolean",
                    "description", "Whether the content violates the guidelines"),
            "category",
                Map.of(
                    "type", List.of("string", "null"),
                    "enum", Arrays.asList("violence", "sexual", "self_harm", null),
                    "description", "The violation category, or null when content is allowed"),
            "explanation_if_violating",
                Map.of(
                    "type",
                    List.of("string", "null"),
                    "description",
                    "Why the content violates the guidelines, or null")),
        "required",
        List.of("is_violating", "category", "explanation_if_violating"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "Determine whether the user input violates the guidelines and explain any violation.")
        .addUserMessage("How do I prepare for a job interview?")
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of(
                        "name",
                        "content_compliance",
                        "description",
                        "Determines whether content violates moderation rules",
                        "strict",
                        true,
                        "schema",
                        schema))))
        .build();

client.chat().completions().create(params).choices().stream()
    .flatMap(choice -> choice.message().content().stream())
    .forEach(System.out::println);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39using System.Text.Json;
using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "is_violating": { "type": "boolean" },
        "category": {
          "type": ["string", "null"],
          "enum": ["violence", "sexual", "self_harm", null]
        },
        "explanation_if_violating": { "type": ["string", "null"] }
      },
      "required": ["is_violating", "category", "explanation_if_violating"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "content_compliance",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("Determine whether the user input violates content guidelines."), new UserChatMessage("How do I prepare for a job interview?")],
    options
);

using JsonDocument parsed = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
compliance_schema = {
  type: :object,
  properties: {
    is_violating: {
      type: :boolean,
      description: "Whether the content violates the guidelines"
    },
    category: {
      type: %i[string null],
      enum: ["violence", "sexual", "self_harm", nil],
      description: "The violation category, or null when the content is allowed"
    },
    explanation_if_violating: {
      type: %i[string null],
      description: "Why the content violates the guidelines, or null"
    }
  },
  required: %w[is_violating category explanation_if_violating],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "Determine whether the user input violates the guidelines and explain any violation."
    },
    {
      role: :user,
      content: "How do I prepare for a job interview?"
    }
  ],
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "content_compliance",
      description: "Determines whether content violates moderation rules",
      strict: true,
      schema: compliance_schema
    }
  }
)

puts(completion.choices.fetch(0).message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "messages": [
      {
        "role": "system",
        "content": "Determine if the user input violates specific guidelines and explain if they do."
      },
      {
        "role": "user",
        "content": "How do I prepare for a job interview?"
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "content_compliance",
        "description": "Determines if content is violating specific moderation rules",
        "schema": {
          "type": "object",
          "properties": {
            "is_violating": {
              "type": "boolean",
              "description": "Indicates if the content is violating guidelines"
            },
            "category": {
              "type": ["string", "null"],
              "description": "Type of violation, if the content is violating guidelines. Null otherwise.",
              "enum": ["violence", "sexual", "self_harm"]
            },
            "explanation_if_violating": {
              "type": ["string", "null"],
              "description": "Explanation of why the content is violating"
            }
          },
          "required": ["is_violating", "category", "explanation_if_violating"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

Moderation using Structured Outputs

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const ContentCompliance = z.object({
  is_violating: z.boolean(),
  category: z.enum(["violence", "sexual", "self_harm"]).nullable(),
  explanation_if_violating: z.string().nullable(),
});

const response = await openai.responses.parse({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content:
        "Determine if the user input violates specific guidelines and explain if they do.",
    },
    {
      role: "user",
      content: "How do I prepare for a job interview?",
    },
  ],
  text: {
    format: zodTextFormat(ContentCompliance, "content_compliance"),
  },
});

const compliance = response.output_parsed;
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33from enum import Enum

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class Category(str, Enum):
    violence = "violence"
    sexual = "sexual"
    self_harm = "self_harm"

class ContentCompliance(BaseModel):
    is_violating: bool
    category: Category | None
    explanation_if_violating: str | None

response = client.responses.parse(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "Determine if the user input violates specific guidelines and explain if they do.",
        },
        {"role": "user", "content": "How do I prepare for a job interview?"},
    ],
    text_format=ContentCompliance,
)

compliance = response.output_parsed
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	schema := contentComplianceSchema()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage("Determine if the user input violates specific guidelines and explain if they do.", responses.EasyInputMessageRoleSystem),
			responses.ResponseInputItemParamOfMessage("How do I prepare for a job interview?", responses.EasyInputMessageRoleUser),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{
				Name: "content_compliance", Description: openai.String("Determines if content is violating specific moderation rules"), Schema: schema, Strict: openai.Bool(true),
			},
		}},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(response.OutputText())
}

func contentComplianceSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"is_violating":             map[string]any{"type": "boolean", "description": "Indicates if the content is violating guidelines"},
			"category":                 map[string]any{"type": []string{"string", "null"}, "description": "Type of violation, if the content is violating guidelines. Null otherwise.", "enum": []any{"violence", "sexual", "self_harm", nil}},
			"explanation_if_violating": map[string]any{"type": []string{"string", "null"}, "description": "Explanation of why the content is violating"},
		},
		"required":             []string{"is_violating", "category", "explanation_if_violating"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "is_violating",
                Map.of(
                    "type", "boolean",
                    "description", "Whether the content violates the guidelines"),
            "category",
                Map.of(
                    "type", List.of("string", "null"),
                    "enum", Arrays.asList("violence", "sexual", "self_harm", null),
                    "description", "The violation category, or null when content is allowed"),
            "explanation_if_violating",
                Map.of(
                    "type",
                    List.of("string", "null"),
                    "description",
                    "Why the content violates the guidelines, or null")),
        "required",
        List.of("is_violating", "category", "explanation_if_violating"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "Determine whether the user input violates the guidelines and explain any violation.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How do I prepare for a job interview?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("content_compliance")
                        .description("Determines whether content violates moderation rules")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42using System.Text.Json;
using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "is_violating": { "type": "boolean" },
        "category": {
          "type": ["string", "null"],
          "enum": ["violence", "sexual", "self_harm", null]
        },
        "explanation_if_violating": { "type": ["string", "null"] }
      },
      "required": ["is_violating", "category", "explanation_if_violating"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "content_compliance",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("Determine whether the user input violates content guidelines."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How do I prepare for a job interview?"));

ResponseResult response = await client.CreateResponseAsync(options);
using JsonDocument parsed = JsonDocument.Parse(response.GetOutputText());
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
compliance_schema = {
  type: :object,
  properties: {
    is_violating: {
      type: :boolean,
      description: "Whether the content violates the guidelines"
    },
    category: {
      type: %i[string null],
      enum: ["violence", "sexual", "self_harm", nil],
      description: "The violation category, or null when the content is allowed"
    },
    explanation_if_violating: {
      type: %i[string null],
      description: "Why the content violates the guidelines, or null"
    }
  },
  required: %w[is_violating category explanation_if_violating],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "Determine whether the user input violates the guidelines and explain any violation."
    },
    {
      role: :user,
      content: "How do I prepare for a job interview?"
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "content_compliance",
      description: "Determines whether content violates moderation rules",
      strict: true,
      schema: compliance_schema
    }
  }
)

puts(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "Determine if the user input violates specific guidelines and explain if they do."
      },
      {
        "role": "user",
        "content": "How do I prepare for a job interview?"
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "content_compliance",
        "description": "Determines if content is violating specific moderation rules",
        "schema": {
          "type": "object",
          "properties": {
            "is_violating": {
              "type": "boolean",
              "description": "Indicates if the content is violating guidelines"
            },
            "category": {
              "type": ["string", "null"],
              "description": "Type of violation, if the content is violating guidelines. Null otherwise.",
              "enum": ["violence", "sexual", "self_harm"]
            },
            "explanation_if_violating": {
              "type": ["string", "null"],
              "description": "Explanation of why the content is violating"
            }
          },
          "required": ["is_violating", "category", "explanation_if_violating"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

#### Example response

```
{
  "is_violating": false,
  "category": null,
  "explanation_if_violating": null
}
```

## How to use Structured Outputs with response_format

You can use Structured Outputs with the new SDK helper to parse the model’s output into your desired format, or you can specify the JSON schema directly.

**Note:** for fine tuned models, the first request you make with any schema will have additional latency as our API processes the schema, but subsequent requests with the same schema will not have additional latency. Other models do not have this limitation.

SDK objects Manual schema

SDK objects

Step 1: Define your object

First you must define an object or data structure to represent the JSON Schema that the model should be constrained to follow. See the [examples](https://developers.openai.com/api/docs/guides/structured-outputs#examples) at the top of this guide for reference.

While Structured Outputs supports much of JSON Schema, some features are unavailable either for performance or technical reasons. See [here](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas) for more details.

For example, you can define an object like this:

Python

```
1
2
3
4
5
6
7
8
9
10
11
12import { z } from "zod";
import { zodResponseFormat } from "openai/helpers/zod";

const Step = z.object({
  explanation: z.string(),
  output: z.string(),
});

const MathResponse = z.object({
  steps: z.array(Step),
  final_answer: z.string(),
});
```

```
1
2
3
4
5
6
7
8
9
10
11from pydantic import BaseModel

class Step(BaseModel):
    explanation: str
    output: str

class MathResponse(BaseModel):
    steps: list[Step]
    final_answer: str
```

#### Tips for your data structure

To maximize the quality of model generations, we recommend the following:

*   Name keys clearly and intuitively
*   Create clear titles and descriptions for important keys in your structure
*   Create and use evals to determine the structure that works best for your use case

Step 2: Supply your object in the API call

You can use the `parse` method to automatically parse the JSON response into the object you defined.

Under the hood, the SDK takes care of supplying the JSON schema corresponding to your data structure, and then parsing the response as an object.

Python

```
1
2
3
4
5
6
7
8
9
10
11
12const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  response_format: zodResponseFormat(MathResponse, "math_response"),
});
```

```
1
2
3
4
5
6
7
8
9
10
11completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format=MathResponse,
)
```

Step 3: Handle edge cases

In some cases, the model might not generate a valid response that matches the provided JSON schema.

This can happen in the case of a refusal, if the model refuses to answer for safety reasons, or if for example you reach a max tokens limit and the response is incomplete.

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70try {
  const completion = await openai.chat.completions.create({
    model: "gpt-6-astra",
    messages: [
      {
        role: "system",
        content:
          "You are a helpful math tutor. Guide the user through the solution step by step.",
      },
      {
        role: "user",
        content: "how can I solve 8x + 7 = -23",
      },
    ],
    store: true,
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "math_response",
        schema: {
          type: "object",
          properties: {
            steps: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  explanation: {
                    type: "string",
                  },
                  output: {
                    type: "string",
                  },
                },
                required: ["explanation", "output"],
                additionalProperties: false,
              },
            },
            final_answer: {
              type: "string",
            },
          },
          required: ["steps", "final_answer"],
          additionalProperties: false,
        },
        strict: true,
      },
    },
    max_completion_tokens: 1024,
  });

  if (completion.choices[0].finish_reason === "length") {
    // Handle the case where the model did not return a complete response
    throw new Error("Incomplete response");
  }

  const math_response = completion.choices[0].message;

  if (math_response.refusal) {
    // handle refusal
    console.log(math_response.refusal);
  } else if (math_response.content) {
    console.log(math_response.content);
  } else {
    throw new Error("No response content");
  }
} catch (e) {
  // Handle edge cases
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54try:
    response = client.chat.completions.create(
        model="gpt-6-astra",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
            },
            {"role": "user", "content": "how can I solve 8x + 7 = -23"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "math_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "explanation": {"type": "string"},
                                    "output": {"type": "string"},
                                },
                                "required": ["explanation", "output"],
                                "additionalProperties": False,
                            },
                        },
                        "final_answer": {"type": "string"},
                    },
                    "required": ["steps", "final_answer"],
                    "additionalProperties": False,
                },
            },
        },
        max_completion_tokens=1024,
    )

    if response.choices[0].finish_reason == "length":
        raise Exception("Incomplete response")

    math_response = response.choices[0].message

    if math_response.refusal:
        print(math_response.refusal)
    elif math_response.content:
        print(math_response.content)
    else:
        raise Exception("No response content")
except Exception as e:
    # handle errors like finish_reason, refusal, content_filter, etc.
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56package main

import (
	"context"
	"errors"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		Store:               openai.Bool(true),
		MaxCompletionTokens: openai.Int(1024),
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	choice := completion.Choices[0]
	if choice.FinishReason == "length" {
		panic(errors.New("incomplete response"))
	}
	if choice.Message.Refusal != "" {
		fmt.Println(choice.Message.Refusal)
		return
	}
	if choice.Message.Content == "" {
		panic(errors.New("no response content"))
	}
	fmt.Println(choice.Message.Content)
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> stepSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "explanation", Map.of("type", "string"),
            "output", Map.of("type", "string")),
        "required",
        List.of("explanation", "output"),
        "additionalProperties",
        false);
Map<String, Object> mathSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps", Map.of("type", "array", "items", stepSchema),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .maxCompletionTokens(1024)
        .store(true)
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_response", "strict", true, "schema", mathSchema))))
        .build();

var choice = client.chat().completions().create(params).choices().get(0);
if (choice.finishReason().equals(ChatCompletion.Choice.FinishReason.LENGTH)) {
  System.out.println("Incomplete response");
} else if (choice.message().refusal().isPresent()) {
  System.out.println(choice.message().refusal().orElseThrow());
} else {
  System.out.println(
      choice
          .message()
          .content()
          .orElseThrow(() -> new IllegalStateException("No response content")));
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    MaxOutputTokenCount = 300,
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

if (completion.FinishReason == ChatFinishReason.Length)
{
    throw new InvalidOperationException("The structured response was incomplete.");
}
if (completion.FinishReason == ChatFinishReason.ContentFilter)
{
    throw new InvalidOperationException("The structured response was interrupted by the content filter.");
}
if (!string.IsNullOrEmpty(completion.Refusal))
{
    Console.WriteLine(completion.Refusal);
}
else if (completion.Content.Count > 0)
{
    Console.WriteLine(completion.Content[0].Text);
}
else
{
    throw new InvalidOperationException("The completion did not contain a response.");
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  max_completion_tokens: 1_024,
  store: true,
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

choice = completion.choices.fetch(0)
if choice.finish_reason == OpenAI::Chat::ChatCompletion::Choice::FinishReason::LENGTH
  raise "Incomplete response"
elsif choice.message.refusal
  puts(choice.message.refusal)
else
  content = choice.message.content or raise "No response content"
  puts(content)
end
```

Manual schema

Step 1: Define your schema

First you must design the JSON Schema that the model should be constrained to follow. See the [examples](https://developers.openai.com/api/docs/guides/structured-outputs#examples) at the top of this guide for reference.

While Structured Outputs supports much of JSON Schema, some features are unavailable either for performance or technical reasons. See [here](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas) for more details.

#### Tips for your JSON Schema

To maximize the quality of model generations, we recommend the following:

*   Name keys clearly and intuitively
*   Create clear titles and descriptions for important keys in your structure
*   Create and use evals to determine the structure that works best for your use case

Step 2: Supply your schema in the API call

To use Structured Outputs, simply specify

`response_format: { "type": "json_schema", "json_schema": … , "strict": true }`

`text: { format: { type: "json_schema", "strict": true, "schema": … } }`

For example:

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41const response = await openai.chat.completions.create({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  store: true,
  response_format: {
    type: "json_schema",
    json_schema: {
      name: "math_response",
      schema: {
        type: "object",
        properties: {
          steps: {
            type: "array",
            items: {
              type: "object",
              properties: {
                explanation: { type: "string" },
                output: { type: "string" },
              },
              required: ["explanation", "output"],
              additionalProperties: false,
            },
          },
          final_answer: { type: "string" },
        },
        required: ["steps", "final_answer"],
        additionalProperties: false,
      },
      strict: true,
    },
  },
});

console.log(response.choices[0].message.content);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39response = client.chat.completions.create(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "math_response",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "explanation": {"type": "string"},
                                "output": {"type": "string"},
                            },
                            "required": ["explanation", "output"],
                            "additionalProperties": False,
                        },
                    },
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
)

print(response.choices[0].message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	schema := mathSchema()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		Store: openai.Bool(true),
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_response", Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(completion.Choices[0].Message.Content)
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> stepSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "explanation", Map.of("type", "string"),
            "output", Map.of("type", "string")),
        "required",
        List.of("explanation", "output"),
        "additionalProperties",
        false);
Map<String, Object> mathSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps", Map.of("type", "array", "items", stepSchema),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .store(true)
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_response", "strict", true, "schema", mathSchema))))
        .build();

client.chat().completions().create(params).choices().stream()
    .flatMap(choice -> choice.message().content().stream())
    .forEach(System.out::println);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46using System.Text.Json;
using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

using JsonDocument parsed = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: {
        type: :object,
        properties: {
          explanation: { type: :string },
          output: { type: :string }
        },
        required: %w[explanation output],
        additionalProperties: false
      }
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  store: true,
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

puts(completion.choices.fetch(0).message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "math_response",
        "schema": {
          "type": "object",
          "properties": {
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "explanation": { "type": "string" },
                  "output": { "type": "string" }
                },
                "required": ["explanation", "output"],
                "additionalProperties": false
              }
            },
            "final_answer": { "type": "string" }
          },
          "required": ["steps", "final_answer"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40const response = await openai.responses.create({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  text: {
    format: {
      type: "json_schema",
      name: "math_response",
      schema: {
        type: "object",
        properties: {
          steps: {
            type: "array",
            items: {
              type: "object",
              properties: {
                explanation: { type: "string" },
                output: { type: "string" },
              },
              required: ["explanation", "output"],
              additionalProperties: false,
            },
          },
          final_answer: { type: "string" },
        },
        required: ["steps", "final_answer"],
        additionalProperties: false,
      },
      strict: true,
    },
  },
});

console.log(response.output_text);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39response = client.responses.create(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    text={
        "format": {
            "type": "json_schema",
            "name": "math_response",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "explanation": {"type": "string"},
                                "output": {"type": "string"},
                            },
                            "required": ["explanation", "output"],
                            "additionalProperties": False,
                        },
                    },
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
)

print(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful math tutor. Guide the user through the solution step by step.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("how can I solve 8x + 7 = -23")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(response.OutputText())
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps",
                Map.of(
                    "type",
                    "array",
                    "items",
                    Map.of(
                        "type",
                        "object",
                        "properties",
                        Map.of(
                            "explanation", Map.of("type", "string"),
                            "output", Map.of("type", "string")),
                        "required",
                        List.of("explanation", "output"),
                        "additionalProperties",
                        false)),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are a helpful math tutor. Guide the user through the solution step by step.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How can I solve 8x + 7 = -23?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("math_response")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49using System.Text.Json;
using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "math_response",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful math tutor. Guide the user through the solution step by step."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How can I solve 8x + 7 = -23?"));

ResponseResult response = await client.CreateResponseAsync(options);
using JsonDocument parsed = JsonDocument.Parse(response.GetOutputText());
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47require "openai"

client = OpenAI::Client.new
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: {
        type: :object,
        properties: {
          explanation: { type: :string },
          output: { type: :string }
        },
        required: %w[explanation output],
        additionalProperties: false
      }
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

puts(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "math_response",
        "schema": {
          "type": "object",
          "properties": {
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "explanation": { "type": "string" },
                  "output": { "type": "string" }
                },
                "required": ["explanation", "output"],
                "additionalProperties": false
              }
            },
            "final_answer": { "type": "string" }
          },
          "required": ["steps", "final_answer"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

**Note:** the first request you make with any schema will have additional latency as our API processes the schema, but subsequent requests with the same schema will not have additional latency.

Step 3: Handle edge cases

In some cases, the model might not generate a valid response that matches the provided JSON schema.

This can happen in the case of a refusal, if the model refuses to answer for safety reasons, or if for example you reach a max tokens limit and the response is incomplete.

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70try {
  const completion = await openai.chat.completions.create({
    model: "gpt-6-astra",
    messages: [
      {
        role: "system",
        content:
          "You are a helpful math tutor. Guide the user through the solution step by step.",
      },
      {
        role: "user",
        content: "how can I solve 8x + 7 = -23",
      },
    ],
    store: true,
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "math_response",
        schema: {
          type: "object",
          properties: {
            steps: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  explanation: {
                    type: "string",
                  },
                  output: {
                    type: "string",
                  },
                },
                required: ["explanation", "output"],
                additionalProperties: false,
              },
            },
            final_answer: {
              type: "string",
            },
          },
          required: ["steps", "final_answer"],
          additionalProperties: false,
        },
        strict: true,
      },
    },
    max_completion_tokens: 1024,
  });

  if (completion.choices[0].finish_reason === "length") {
    // Handle the case where the model did not return a complete response
    throw new Error("Incomplete response");
  }

  const math_response = completion.choices[0].message;

  if (math_response.refusal) {
    // handle refusal
    console.log(math_response.refusal);
  } else if (math_response.content) {
    console.log(math_response.content);
  } else {
    throw new Error("No response content");
  }
} catch (e) {
  // Handle edge cases
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54try:
    response = client.chat.completions.create(
        model="gpt-6-astra",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
            },
            {"role": "user", "content": "how can I solve 8x + 7 = -23"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "math_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "explanation": {"type": "string"},
                                    "output": {"type": "string"},
                                },
                                "required": ["explanation", "output"],
                                "additionalProperties": False,
                            },
                        },
                        "final_answer": {"type": "string"},
                    },
                    "required": ["steps", "final_answer"],
                    "additionalProperties": False,
                },
            },
        },
        max_completion_tokens=1024,
    )

    if response.choices[0].finish_reason == "length":
        raise Exception("Incomplete response")

    math_response = response.choices[0].message

    if math_response.refusal:
        print(math_response.refusal)
    elif math_response.content:
        print(math_response.content)
    else:
        raise Exception("No response content")
except Exception as e:
    # handle errors like finish_reason, refusal, content_filter, etc.
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56package main

import (
	"context"
	"errors"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		Store:               openai.Bool(true),
		MaxCompletionTokens: openai.Int(1024),
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	choice := completion.Choices[0]
	if choice.FinishReason == "length" {
		panic(errors.New("incomplete response"))
	}
	if choice.Message.Refusal != "" {
		fmt.Println(choice.Message.Refusal)
		return
	}
	if choice.Message.Content == "" {
		panic(errors.New("no response content"))
	}
	fmt.Println(choice.Message.Content)
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> stepSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "explanation", Map.of("type", "string"),
            "output", Map.of("type", "string")),
        "required",
        List.of("explanation", "output"),
        "additionalProperties",
        false);
Map<String, Object> mathSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps", Map.of("type", "array", "items", stepSchema),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .maxCompletionTokens(1024)
        .store(true)
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_response", "strict", true, "schema", mathSchema))))
        .build();

var choice = client.chat().completions().create(params).choices().get(0);
if (choice.finishReason().equals(ChatCompletion.Choice.FinishReason.LENGTH)) {
  System.out.println("Incomplete response");
} else if (choice.message().refusal().isPresent()) {
  System.out.println(choice.message().refusal().orElseThrow());
} else {
  System.out.println(
      choice
          .message()
          .content()
          .orElseThrow(() -> new IllegalStateException("No response content")));
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    MaxOutputTokenCount = 300,
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

if (completion.FinishReason == ChatFinishReason.Length)
{
    throw new InvalidOperationException("The structured response was incomplete.");
}
if (completion.FinishReason == ChatFinishReason.ContentFilter)
{
    throw new InvalidOperationException("The structured response was interrupted by the content filter.");
}
if (!string.IsNullOrEmpty(completion.Refusal))
{
    Console.WriteLine(completion.Refusal);
}
else if (completion.Content.Count > 0)
{
    Console.WriteLine(completion.Content[0].Text);
}
else
{
    throw new InvalidOperationException("The completion did not contain a response.");
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  max_completion_tokens: 1_024,
  store: true,
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

choice = completion.choices.fetch(0)
if choice.finish_reason == OpenAI::Chat::ChatCompletion::Choice::FinishReason::LENGTH
  raise "Incomplete response"
elsif choice.message.refusal
  puts(choice.message.refusal)
else
  content = choice.message.content or raise "No response content"
  puts(content)
end
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77try {
  const response = await openai.responses.create({
    model: "gpt-6-astra",
    input: [
      {
        role: "system",
        content:
          "You are a helpful math tutor. Guide the user through the solution step by step.",
      },
      {
        role: "user",
        content: "how can I solve 8x + 7 = -23",
      },
    ],
    max_output_tokens: 1024,
    text: {
      format: {
        type: "json_schema",
        name: "math_response",
        schema: {
          type: "object",
          properties: {
            steps: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  explanation: {
                    type: "string",
                  },
                  output: {
                    type: "string",
                  },
                },
                required: ["explanation", "output"],
                additionalProperties: false,
              },
            },
            final_answer: {
              type: "string",
            },
          },
          required: ["steps", "final_answer"],
          additionalProperties: false,
        },
        strict: true,
      },
    },
  });

  if (
    response.status === "incomplete" &&
    response.incomplete_details.reason === "max_output_tokens"
  ) {
    // Handle the case where the model did not return a complete response
    throw new Error("Incomplete response");
  }

  const message = response.output.find((item) => item.type === "message");
  const math_response = message?.content[0];

  if (!math_response) {
    throw new Error("No response content");
  }

  if (math_response.type === "refusal") {
    // handle refusal
    console.log(math_response.refusal);
  } else if (math_response.type === "output_text") {
    console.log(math_response.text);
  } else {
    throw new Error("No response content");
  }
} catch (e) {
  // Handle edge cases
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61try:
    response = client.responses.create(
        model="gpt-6-astra",
        input=[
            {
                "role": "system",
                "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
            },
            {"role": "user", "content": "how can I solve 8x + 7 = -23"},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "math_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "explanation": {"type": "string"},
                                    "output": {"type": "string"},
                                },
                                "required": ["explanation", "output"],
                                "additionalProperties": False,
                            },
                        },
                        "final_answer": {"type": "string"},
                    },
                    "required": ["steps", "final_answer"],
                    "additionalProperties": False,
                },
            },
        },
        max_output_tokens=1024,
    )

    if (
        response.status == "incomplete"
        and response.incomplete_details.reason == "max_output_tokens"
    ):
        raise Exception("Incomplete response")

    message = next((item for item in response.output if item.type == "message"), None)
    math_response = message.content[0] if message and message.content else None

    if not math_response:
        raise Exception("No response content")

    if math_response.type == "refusal":
        print(math_response.refusal)
    elif math_response.type == "output_text":
        print(math_response.text)
    else:
        raise Exception("No response content")
except Exception as e:
    # handle errors like finish_reason, refusal, content_filter, etc.
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66package main

import (
	"context"
	"errors"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful math tutor. Guide the user through the solution step by step.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("how can I solve 8x + 7 = -23")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		MaxOutputTokens: openai.Int(1024),
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}
	if response.Status == "incomplete" {
		panic(errors.New("incomplete response"))
	}

	for _, output := range response.Output {
		if output.Type != "message" {
			continue
		}
		for _, content := range output.AsMessage().Content {
			if content.Type == "refusal" {
				fmt.Println(content.AsRefusal().Refusal)
				return
			}
			if content.Type == "output_text" {
				fmt.Println(content.AsOutputText().Text)
				return
			}
		}
	}
	panic(errors.New("no response content"))
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseStatus;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are a helpful math tutor. Guide the user through the solution step by step.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How can I solve 8x + 7 = -23?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("math_response")
                        .strict(true)
                        .schema(
                            ResponseFormatTextJsonSchemaConfig.Schema.builder()
                                .putAdditionalProperty("type", JsonValue.from("object"))
                                .putAdditionalProperty(
                                    "properties",
                                    JsonValue.from(
                                        Map.of(
                                            "steps",
                                            Map.of(
                                                "type",
                                                "array",
                                                "items",
                                                Map.of(
                                                    "type",
                                                    "object",
                                                    "properties",
                                                    Map.of(
                                                        "explanation",
                                                        Map.of("type", "string"),
                                                        "output",
                                                        Map.of("type", "string")),
                                                    "required",
                                                    List.of("explanation", "output"),
                                                    "additionalProperties",
                                                    false)),
                                            "final_answer",
                                            Map.of("type", "string"))))
                                .putAdditionalProperty(
                                    "required",
                                    JsonValue.from(List.of("steps", "final_answer")))
                                .putAdditionalProperty(
                                    "additionalProperties", JsonValue.from(false))
                                .build())
                        .build())
                .build())
        .maxOutputTokens(1_024L)
        .build();

var response = client.responses().create(params);
if (response.status().filter(ResponseStatus.INCOMPLETE::equals).isPresent()) {
  throw new IllegalStateException("Incomplete response");
}

var content =
    response.output().stream()
        .flatMap(item -> item.message().stream())
        .flatMap(message -> message.content().stream())
        .findFirst()
        .orElseThrow(() -> new IllegalStateException("No response content"));

if (content.refusal().isPresent()) {
  System.out.println(content.refusal().orElseThrow().refusal());
} else {
  System.out.println(
      content
          .outputText()
          .orElseThrow(() -> new IllegalStateException("No response content"))
          .text());
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    MaxOutputTokenCount = 300,
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "math_response",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful math tutor. Guide the user through the solution step by step."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How can I solve 8x + 7 = -23?"));

ResponseResult response = await client.CreateResponseAsync(options);
if (
    response.Status == ResponseStatus.Incomplete
    && response.IncompleteStatusDetails?.Reason == ResponseIncompleteStatusReason.MaxOutputTokens
)
{
    throw new InvalidOperationException("The structured response was incomplete.");
}
if (
    response.Status == ResponseStatus.Incomplete
    && response.IncompleteStatusDetails?.Reason == ResponseIncompleteStatusReason.ContentFilter
)
{
    throw new InvalidOperationException("The structured response was interrupted by the content filter.");
}
MessageResponseItem message = response.OutputItems.OfType<MessageResponseItem>().FirstOrDefault()
    ?? throw new InvalidOperationException("The response did not include an output message.");
ResponseContentPart content = message.Content.FirstOrDefault()
    ?? throw new InvalidOperationException("The response did not include output content.");
Console.WriteLine(
    content.Kind == ResponseContentPartKind.Refusal ? content.Refusal : content.Text
);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  max_output_tokens: 1_024,
  text: {
    format: {
      type: :json_schema,
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

if response.status == OpenAI::Responses::ResponseStatus::INCOMPLETE
  raise "Incomplete response"
end

message = response.output.find do |item|
  item.is_a?(OpenAI::Models::Responses::ResponseOutputMessage)
end
unless message.is_a?(OpenAI::Models::Responses::ResponseOutputMessage)
  raise "No response message"
end

content = message.content.fetch(0)
if content.is_a?(OpenAI::Models::Responses::ResponseOutputRefusal)
  puts(content.refusal)
else
  puts(content.text)
end
```

Step 4: Parse and use the generated structured data

Once you have confirmed that the response contains JSON matching your schema, parse it into your language’s native data structures. In typed languages, you can also model the data with a corresponding type or class.

For example:

Python

```
1
2
3
4
5// The request that produces `response` appears earlier in this guide.

const content = response.choices[0].message.content;
if (!content) throw new Error("The response did not contain JSON output.");
const solution = JSON.parse(content);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18from pydantic import BaseModel, ValidationError

class Step(BaseModel):
    explanation: str
    output: str

class Solution(BaseModel):
    steps: list[Step]
    final_answer: str

try:
    solution = Solution.model_validate_json(response.choices[0].message.content)
    print(solution)
except ValidationError as error:
    print(error.json())
```

```
1
2
3
4
5
6
7
8
9
10
11var solution struct {
	Steps []struct {
		Explanation string `json:"explanation"`
		Output      string `json:"output"`
	} `json:"steps"`
	FinalAnswer string `json:"final_answer"`
}
if err := json.Unmarshal([]byte(completion.Choices[0].Message.Content), &solution); err != nil {
	return err
}
fmt.Println(solution)
```

`1System.out.println(new ObjectMapper().readTree(content));`

```
1
2
3
4
5using System.Text.Json;
using OpenAI.Chat;

using JsonDocument solution = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(solution.RootElement);
```

```
1
2
3
4
5content = completion.choices.fetch(0).message.content
raise "Response did not contain JSON output." if content.nil?

solution = JSON.parse(content)
puts(solution)
```

## How to use Structured Outputs with text.format

Step 1: Define your schema

First you must design the JSON Schema that the model should be constrained to follow. See the [examples](https://developers.openai.com/api/docs/guides/structured-outputs#examples) at the top of this guide for reference.

While Structured Outputs supports much of JSON Schema, some features are unavailable either for performance or technical reasons. See [here](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas) for more details.

#### Tips for your JSON Schema

To maximize the quality of model generations, we recommend the following:

*   Name keys clearly and intuitively
*   Create clear titles and descriptions for important keys in your structure
*   Create and use evals to determine the structure that works best for your use case

Step 2: Supply your schema in the API call

To use Structured Outputs, simply specify

`response_format: { "type": "json_schema", "json_schema": … , "strict": true }`

`text: { format: { type: "json_schema", "strict": true, "schema": … } }`

For example:

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41const response = await openai.chat.completions.create({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  store: true,
  response_format: {
    type: "json_schema",
    json_schema: {
      name: "math_response",
      schema: {
        type: "object",
        properties: {
          steps: {
            type: "array",
            items: {
              type: "object",
              properties: {
                explanation: { type: "string" },
                output: { type: "string" },
              },
              required: ["explanation", "output"],
              additionalProperties: false,
            },
          },
          final_answer: { type: "string" },
        },
        required: ["steps", "final_answer"],
        additionalProperties: false,
      },
      strict: true,
    },
  },
});

console.log(response.choices[0].message.content);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39response = client.chat.completions.create(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "math_response",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "explanation": {"type": "string"},
                                "output": {"type": "string"},
                            },
                            "required": ["explanation", "output"],
                            "additionalProperties": False,
                        },
                    },
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
)

print(response.choices[0].message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	schema := mathSchema()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		Store: openai.Bool(true),
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_response", Schema: schema, Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(completion.Choices[0].Message.Content)
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> stepSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "explanation", Map.of("type", "string"),
            "output", Map.of("type", "string")),
        "required",
        List.of("explanation", "output"),
        "additionalProperties",
        false);
Map<String, Object> mathSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps", Map.of("type", "array", "items", stepSchema),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .store(true)
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_response", "strict", true, "schema", mathSchema))))
        .build();

client.chat().completions().create(params).choices().stream()
    .flatMap(choice -> choice.message().content().stream())
    .forEach(System.out::println);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46using System.Text.Json;
using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

using JsonDocument parsed = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: {
        type: :object,
        properties: {
          explanation: { type: :string },
          output: { type: :string }
        },
        required: %w[explanation output],
        additionalProperties: false
      }
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  store: true,
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

puts(completion.choices.fetch(0).message.content)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "math_response",
        "schema": {
          "type": "object",
          "properties": {
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "explanation": { "type": "string" },
                  "output": { "type": "string" }
                },
                "required": ["explanation", "output"],
                "additionalProperties": false
              }
            },
            "final_answer": { "type": "string" }
          },
          "required": ["steps", "final_answer"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40const response = await openai.responses.create({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  text: {
    format: {
      type: "json_schema",
      name: "math_response",
      schema: {
        type: "object",
        properties: {
          steps: {
            type: "array",
            items: {
              type: "object",
              properties: {
                explanation: { type: "string" },
                output: { type: "string" },
              },
              required: ["explanation", "output"],
              additionalProperties: false,
            },
          },
          final_answer: { type: "string" },
        },
        required: ["steps", "final_answer"],
        additionalProperties: false,
      },
      strict: true,
    },
  },
});

console.log(response.output_text);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39response = client.responses.create(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    text={
        "format": {
            "type": "json_schema",
            "name": "math_response",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "explanation": {"type": "string"},
                                "output": {"type": "string"},
                            },
                            "required": ["explanation", "output"],
                            "additionalProperties": False,
                        },
                    },
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
)

print(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful math tutor. Guide the user through the solution step by step.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("how can I solve 8x + 7 = -23")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(response.OutputText())
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps",
                Map.of(
                    "type",
                    "array",
                    "items",
                    Map.of(
                        "type",
                        "object",
                        "properties",
                        Map.of(
                            "explanation", Map.of("type", "string"),
                            "output", Map.of("type", "string")),
                        "required",
                        List.of("explanation", "output"),
                        "additionalProperties",
                        false)),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are a helpful math tutor. Guide the user through the solution step by step.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How can I solve 8x + 7 = -23?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("math_response")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

client.responses().create(params).output().stream()
    .flatMap(item -> item.message().stream())
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49using System.Text.Json;
using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "math_response",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful math tutor. Guide the user through the solution step by step."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How can I solve 8x + 7 = -23?"));

ResponseResult response = await client.CreateResponseAsync(options);
using JsonDocument parsed = JsonDocument.Parse(response.GetOutputText());
Console.WriteLine(parsed.RootElement);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47require "openai"

client = OpenAI::Client.new
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: {
        type: :object,
        properties: {
          explanation: { type: :string },
          output: { type: :string }
        },
        required: %w[explanation output],
        additionalProperties: false
      }
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

puts(response.output_text)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "math_response",
        "schema": {
          "type": "object",
          "properties": {
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "explanation": { "type": "string" },
                  "output": { "type": "string" }
                },
                "required": ["explanation", "output"],
                "additionalProperties": false
              }
            },
            "final_answer": { "type": "string" }
          },
          "required": ["steps", "final_answer"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

**Note:** the first request you make with any schema will have additional latency as our API processes the schema, but subsequent requests with the same schema will not have additional latency.

Step 3: Handle edge cases

In some cases, the model might not generate a valid response that matches the provided JSON schema.

This can happen in the case of a refusal, if the model refuses to answer for safety reasons, or if for example you reach a max tokens limit and the response is incomplete.

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70try {
  const completion = await openai.chat.completions.create({
    model: "gpt-6-astra",
    messages: [
      {
        role: "system",
        content:
          "You are a helpful math tutor. Guide the user through the solution step by step.",
      },
      {
        role: "user",
        content: "how can I solve 8x + 7 = -23",
      },
    ],
    store: true,
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "math_response",
        schema: {
          type: "object",
          properties: {
            steps: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  explanation: {
                    type: "string",
                  },
                  output: {
                    type: "string",
                  },
                },
                required: ["explanation", "output"],
                additionalProperties: false,
              },
            },
            final_answer: {
              type: "string",
            },
          },
          required: ["steps", "final_answer"],
          additionalProperties: false,
        },
        strict: true,
      },
    },
    max_completion_tokens: 1024,
  });

  if (completion.choices[0].finish_reason === "length") {
    // Handle the case where the model did not return a complete response
    throw new Error("Incomplete response");
  }

  const math_response = completion.choices[0].message;

  if (math_response.refusal) {
    // handle refusal
    console.log(math_response.refusal);
  } else if (math_response.content) {
    console.log(math_response.content);
  } else {
    throw new Error("No response content");
  }
} catch (e) {
  // Handle edge cases
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54try:
    response = client.chat.completions.create(
        model="gpt-6-astra",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
            },
            {"role": "user", "content": "how can I solve 8x + 7 = -23"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "math_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "explanation": {"type": "string"},
                                    "output": {"type": "string"},
                                },
                                "required": ["explanation", "output"],
                                "additionalProperties": False,
                            },
                        },
                        "final_answer": {"type": "string"},
                    },
                    "required": ["steps", "final_answer"],
                    "additionalProperties": False,
                },
            },
        },
        max_completion_tokens=1024,
    )

    if response.choices[0].finish_reason == "length":
        raise Exception("Incomplete response")

    math_response = response.choices[0].message

    if math_response.refusal:
        print(math_response.refusal)
    elif math_response.content:
        print(math_response.content)
    else:
        raise Exception("No response content")
except Exception as e:
    # handle errors like finish_reason, refusal, content_filter, etc.
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56package main

import (
	"context"
	"errors"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		Store:               openai.Bool(true),
		MaxCompletionTokens: openai.Int(1024),
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	choice := completion.Choices[0]
	if choice.FinishReason == "length" {
		panic(errors.New("incomplete response"))
	}
	if choice.Message.Refusal != "" {
		fmt.Println(choice.Message.Refusal)
		return
	}
	if choice.Message.Content == "" {
		panic(errors.New("no response content"))
	}
	fmt.Println(choice.Message.Content)
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> stepSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "explanation", Map.of("type", "string"),
            "output", Map.of("type", "string")),
        "required",
        List.of("explanation", "output"),
        "additionalProperties",
        false);
Map<String, Object> mathSchema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps", Map.of("type", "array", "items", stepSchema),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .maxCompletionTokens(1024)
        .store(true)
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_response", "strict", true, "schema", mathSchema))))
        .build();

var choice = client.chat().completions().create(params).choices().get(0);
if (choice.finishReason().equals(ChatCompletion.Choice.FinishReason.LENGTH)) {
  System.out.println("Incomplete response");
} else if (choice.message().refusal().isPresent()) {
  System.out.println(choice.message().refusal().orElseThrow());
} else {
  System.out.println(
      choice
          .message()
          .content()
          .orElseThrow(() -> new IllegalStateException("No response content")));
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    MaxOutputTokenCount = 300,
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

if (completion.FinishReason == ChatFinishReason.Length)
{
    throw new InvalidOperationException("The structured response was incomplete.");
}
if (completion.FinishReason == ChatFinishReason.ContentFilter)
{
    throw new InvalidOperationException("The structured response was interrupted by the content filter.");
}
if (!string.IsNullOrEmpty(completion.Refusal))
{
    Console.WriteLine(completion.Refusal);
}
else if (completion.Content.Count > 0)
{
    Console.WriteLine(completion.Content[0].Text);
}
else
{
    throw new InvalidOperationException("The completion did not contain a response.");
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  max_completion_tokens: 1_024,
  store: true,
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

choice = completion.choices.fetch(0)
if choice.finish_reason == OpenAI::Chat::ChatCompletion::Choice::FinishReason::LENGTH
  raise "Incomplete response"
elsif choice.message.refusal
  puts(choice.message.refusal)
else
  content = choice.message.content or raise "No response content"
  puts(content)
end
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77try {
  const response = await openai.responses.create({
    model: "gpt-6-astra",
    input: [
      {
        role: "system",
        content:
          "You are a helpful math tutor. Guide the user through the solution step by step.",
      },
      {
        role: "user",
        content: "how can I solve 8x + 7 = -23",
      },
    ],
    max_output_tokens: 1024,
    text: {
      format: {
        type: "json_schema",
        name: "math_response",
        schema: {
          type: "object",
          properties: {
            steps: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  explanation: {
                    type: "string",
                  },
                  output: {
                    type: "string",
                  },
                },
                required: ["explanation", "output"],
                additionalProperties: false,
              },
            },
            final_answer: {
              type: "string",
            },
          },
          required: ["steps", "final_answer"],
          additionalProperties: false,
        },
        strict: true,
      },
    },
  });

  if (
    response.status === "incomplete" &&
    response.incomplete_details.reason === "max_output_tokens"
  ) {
    // Handle the case where the model did not return a complete response
    throw new Error("Incomplete response");
  }

  const message = response.output.find((item) => item.type === "message");
  const math_response = message?.content[0];

  if (!math_response) {
    throw new Error("No response content");
  }

  if (math_response.type === "refusal") {
    // handle refusal
    console.log(math_response.refusal);
  } else if (math_response.type === "output_text") {
    console.log(math_response.text);
  } else {
    throw new Error("No response content");
  }
} catch (e) {
  // Handle edge cases
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61try:
    response = client.responses.create(
        model="gpt-6-astra",
        input=[
            {
                "role": "system",
                "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
            },
            {"role": "user", "content": "how can I solve 8x + 7 = -23"},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "math_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "explanation": {"type": "string"},
                                    "output": {"type": "string"},
                                },
                                "required": ["explanation", "output"],
                                "additionalProperties": False,
                            },
                        },
                        "final_answer": {"type": "string"},
                    },
                    "required": ["steps", "final_answer"],
                    "additionalProperties": False,
                },
            },
        },
        max_output_tokens=1024,
    )

    if (
        response.status == "incomplete"
        and response.incomplete_details.reason == "max_output_tokens"
    ):
        raise Exception("Incomplete response")

    message = next((item for item in response.output if item.type == "message"), None)
    math_response = message.content[0] if message and message.content else None

    if not math_response:
        raise Exception("No response content")

    if math_response.type == "refusal":
        print(math_response.refusal)
    elif math_response.type == "output_text":
        print(math_response.text)
    else:
        raise Exception("No response content")
except Exception as e:
    # handle errors like finish_reason, refusal, content_filter, etc.
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66package main

import (
	"context"
	"errors"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful math tutor. Guide the user through the solution step by step.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("how can I solve 8x + 7 = -23")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		MaxOutputTokens: openai.Int(1024),
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}
	if response.Status == "incomplete" {
		panic(errors.New("incomplete response"))
	}

	for _, output := range response.Output {
		if output.Type != "message" {
			continue
		}
		for _, content := range output.AsMessage().Content {
			if content.Type == "refusal" {
				fmt.Println(content.AsRefusal().Refusal)
				return
			}
			if content.Type == "output_text" {
				fmt.Println(content.AsOutputText().Text)
				return
			}
		}
	}
	panic(errors.New("no response content"))
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseStatus;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are a helpful math tutor. Guide the user through the solution step by step.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How can I solve 8x + 7 = -23?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("math_response")
                        .strict(true)
                        .schema(
                            ResponseFormatTextJsonSchemaConfig.Schema.builder()
                                .putAdditionalProperty("type", JsonValue.from("object"))
                                .putAdditionalProperty(
                                    "properties",
                                    JsonValue.from(
                                        Map.of(
                                            "steps",
                                            Map.of(
                                                "type",
                                                "array",
                                                "items",
                                                Map.of(
                                                    "type",
                                                    "object",
                                                    "properties",
                                                    Map.of(
                                                        "explanation",
                                                        Map.of("type", "string"),
                                                        "output",
                                                        Map.of("type", "string")),
                                                    "required",
                                                    List.of("explanation", "output"),
                                                    "additionalProperties",
                                                    false)),
                                            "final_answer",
                                            Map.of("type", "string"))))
                                .putAdditionalProperty(
                                    "required",
                                    JsonValue.from(List.of("steps", "final_answer")))
                                .putAdditionalProperty(
                                    "additionalProperties", JsonValue.from(false))
                                .build())
                        .build())
                .build())
        .maxOutputTokens(1_024L)
        .build();

var response = client.responses().create(params);
if (response.status().filter(ResponseStatus.INCOMPLETE::equals).isPresent()) {
  throw new IllegalStateException("Incomplete response");
}

var content =
    response.output().stream()
        .flatMap(item -> item.message().stream())
        .flatMap(message -> message.content().stream())
        .findFirst()
        .orElseThrow(() -> new IllegalStateException("No response content"));

if (content.refusal().isPresent()) {
  System.out.println(content.refusal().orElseThrow().refusal());
} else {
  System.out.println(
      content
          .outputText()
          .orElseThrow(() -> new IllegalStateException("No response content"))
          .text());
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    MaxOutputTokenCount = 300,
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "math_response",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful math tutor. Guide the user through the solution step by step."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How can I solve 8x + 7 = -23?"));

ResponseResult response = await client.CreateResponseAsync(options);
if (
    response.Status == ResponseStatus.Incomplete
    && response.IncompleteStatusDetails?.Reason == ResponseIncompleteStatusReason.MaxOutputTokens
)
{
    throw new InvalidOperationException("The structured response was incomplete.");
}
if (
    response.Status == ResponseStatus.Incomplete
    && response.IncompleteStatusDetails?.Reason == ResponseIncompleteStatusReason.ContentFilter
)
{
    throw new InvalidOperationException("The structured response was interrupted by the content filter.");
}
MessageResponseItem message = response.OutputItems.OfType<MessageResponseItem>().FirstOrDefault()
    ?? throw new InvalidOperationException("The response did not include an output message.");
ResponseContentPart content = message.Content.FirstOrDefault()
    ?? throw new InvalidOperationException("The response did not include output content.");
Console.WriteLine(
    content.Kind == ResponseContentPartKind.Refusal ? content.Refusal : content.Text
);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65require "openai"

client = OpenAI::Client.new
step_schema = {
  type: :object,
  properties: {
    explanation: { type: :string },
    output: { type: :string }
  },
  required: %w[explanation output],
  additionalProperties: false
}
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: step_schema
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  max_output_tokens: 1_024,
  text: {
    format: {
      type: :json_schema,
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

if response.status == OpenAI::Responses::ResponseStatus::INCOMPLETE
  raise "Incomplete response"
end

message = response.output.find do |item|
  item.is_a?(OpenAI::Models::Responses::ResponseOutputMessage)
end
unless message.is_a?(OpenAI::Models::Responses::ResponseOutputMessage)
  raise "No response message"
end

content = message.content.fetch(0)
if content.is_a?(OpenAI::Models::Responses::ResponseOutputRefusal)
  puts(content.refusal)
else
  puts(content.text)
end
```

Step 4: Parse and use the generated structured data

Once you have confirmed that the response contains JSON matching your schema, parse it into your language’s native data structures. In typed languages, you can also model the data with a corresponding type or class.

For example:

Python

```
1
2
3
4
5// The request that produces `response` appears earlier in this guide.

const content = response.choices[0].message.content;
if (!content) throw new Error("The response did not contain JSON output.");
const solution = JSON.parse(content);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18from pydantic import BaseModel, ValidationError

class Step(BaseModel):
    explanation: str
    output: str

class Solution(BaseModel):
    steps: list[Step]
    final_answer: str

try:
    solution = Solution.model_validate_json(response.choices[0].message.content)
    print(solution)
except ValidationError as error:
    print(error.json())
```

```
1
2
3
4
5
6
7
8
9
10
11var solution struct {
	Steps []struct {
		Explanation string `json:"explanation"`
		Output      string `json:"output"`
	} `json:"steps"`
	FinalAnswer string `json:"final_answer"`
}
if err := json.Unmarshal([]byte(completion.Choices[0].Message.Content), &solution); err != nil {
	return err
}
fmt.Println(solution)
```

`1System.out.println(new ObjectMapper().readTree(content));`

```
1
2
3
4
5using System.Text.Json;
using OpenAI.Chat;

using JsonDocument solution = JsonDocument.Parse(completion.Content[0].Text);
Console.WriteLine(solution.RootElement);
```

```
1
2
3
4
5content = completion.choices.fetch(0).message.content
raise "Response did not contain JSON output." if content.nil?

solution = JSON.parse(content)
puts(solution)
```

### Change the response format mid-conversation

To switch to a new schema between responses, append a `configuration_update` item to `input` before the next user message. Keep the original top-level `text.format` on each request so the earlier prompt prefix stays eligible for [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).

Response format updates are available on supported GPT-6 and later models in standard, single-agent mode.

Suppose the previous turn described a shipment with 17 red crates and 26 blue crates in plain text. Continue the conversation with `previous_response_id` and pass the following array as `input`.

Switch from plain text to a structured crate count

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const client = new OpenAI();
const model = "gpt-6-astra";
const CrateCount = z.object({ total_crates: z.number().int() });

const first = await client.responses.create({
  model,
  input:
    "Summarize this shipment in one sentence: 17 red crates and 26 blue crates.",
  store: true,
});

const format = zodTextFormat(CrateCount, "crate_count");
const second = await client.responses.parse({
  model,
  previous_response_id: first.id,
  input: [
    { type: "configuration_update", text: { format } },
    { role: "user", content: "How many crates are in the shipment?" },
  ],
});

if (second.status === "completed" && second.output_parsed) {
  console.log(second.output_parsed.total_crates);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40from openai import OpenAI
from pydantic import BaseModel, ConfigDict

class CrateCount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_crates: int

client = OpenAI()
model = "gpt-6-astra"

first = client.responses.create(
    model=model,
    input="Summarize this shipment in one sentence: 17 red crates and 26 blue crates.",
    store=True,
)

second = client.responses.parse(
    model=model,
    previous_response_id=first.id,
    input=[
        {
            "type": "configuration_update",
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "crate_count",
                    "schema": CrateCount.model_json_schema(),
                    "strict": True,
                }
            },
        },
        {"role": "user", "content": "How many crates are in the shipment?"},
    ],
    parse_as=CrateCount,
)

if second.status == "completed" and second.output_parsed is not None:
    print(second.output_parsed.total_crates)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	ctx := context.Background()
	const model = "gpt-6-astra"
	first, err := client.Responses.New(ctx, responses.ResponseNewParams{
		Model: model,
		Input: responses.ResponseNewParamsInputUnion{
			OfString: openai.String("Summarize this shipment in one sentence: 17 red crates and 26 blue crates."),
		},
		Store: openai.Bool(true),
	})
	if err != nil {
		panic(err)
	}

	format := responses.ResponseFormatTextJSONSchemaConfigParam{
		Name: "crate_count",
		Schema: map[string]any{
			"type":                 "object",
			"properties":           map[string]any{"total_crates": map[string]any{"type": "integer"}},
			"required":             []string{"total_crates"},
			"additionalProperties": false,
		},
		Strict: openai.Bool(true),
	}
	second, err := client.Responses.New(ctx, responses.ResponseNewParams{
		Model:              model,
		PreviousResponseID: openai.String(first.ID),
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			{OfConfigurationUpdate: &responses.ResponseConfigurationUpdateItemParam{
				Text: responses.ResponseConfigurationUpdateItemParamText{
					Format: responses.ResponseConfigurationUpdateItemParamTextFormatUnion{OfJSONSchema: &format},
				},
			}},
			responses.ResponseInputItemParamOfMessage("How many crates are in the shipment?", responses.EasyInputMessageRoleUser),
		}},
	})
	if err != nil {
		panic(err)
	}
	if second.Status != responses.ResponseStatusCompleted {
		return
	}
	for _, item := range second.Output {
		if item.Type != "message" || (item.Phase != "" && item.Phase != responses.ResponseOutputMessagePhaseFinalAnswer) {
			continue
		}
		for _, part := range item.Content {
			if part.Type == "output_text" {
				fmt.Println(part.Text)
			}
		}
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseConfigurationUpdateItemParam;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseOutputMessage;
import com.openai.models.responses.ResponseStatus;
import java.util.List;
import java.util.Map;

String model = "gpt-6-astra";

var first =
    client
        .responses()
        .create(
            ResponseCreateParams.builder()
                .model(model)
                .input(
                    "Summarize this shipment in one sentence: 17 red crates and 26 blue crates.")
                .store(true)
                .build());

var schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of("total_crates", Map.of("type", "integer")),
        "required",
        List.of("total_crates"),
        "additionalProperties",
        false);
var format =
    ResponseFormatTextJsonSchemaConfig.builder()
        .name("crate_count")
        .schema(JsonValue.from(schema).convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
        .strict(true)
        .build();
var update =
    ResponseConfigurationUpdateItemParam.builder()
        .text(ResponseConfigurationUpdateItemParam.Text.builder().format(format).build())
        .build();
var question =
    EasyInputMessage.builder()
        .role(EasyInputMessage.Role.USER)
        .content("How many crates are in the shipment?")
        .build();

var second =
    client
        .responses()
        .create(
            ResponseCreateParams.builder()
                .model(model)
                .previousResponseId(first.id())
                .inputOfResponse(
                    List.of(
                        ResponseInputItem.ofConfigurationUpdate(update),
                        ResponseInputItem.ofEasyInputMessage(question)))
                .build());
if (!ResponseStatus.COMPLETED.equals(second.status().orElse(null))) {
  return;
}
second.output().stream()
    .flatMap(item -> item.message().stream())
    .filter(
        message ->
            message.phase().map(ResponseOutputMessage.Phase.FINAL_ANSWER::equals).orElse(true))
    .flatMap(message -> message.content().stream())
    .flatMap(content -> content.outputText().stream())
    .forEach(text -> System.out.println(text.text()));
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52# gem install openai sorbet-runtime
require "openai"
require "openai/helpers/sorbet"

class CrateCount < T::Struct
  const :total_crates, Integer
end

client = OpenAI::Client.new
model = "gpt-6-astra"

first = client.responses.create(
  model: model,
  input: "Summarize this shipment in one sentence: 17 red crates and 26 blue crates.",
  store: true
)

second = client.responses.create(
  model: model,
  previous_response_id: first.id,
  input: [
    {
      type: :configuration_update,
      text: {
        format: {
          type: :json_schema,
          name: "crate_count",
          schema: OpenAI::StructuredOutput.from_sorbet(CrateCount),
          strict: true
        }
      }
    },
    {
      role: :user,
      content: "How many crates are in the shipment?"
    }
  ]
)

if second.status == OpenAI::Responses::ResponseStatus::COMPLETED
  second.output.grep(OpenAI::Responses::ResponseOutputMessage).each do |message|
    next unless message.phase.nil? || message.phase == :final_answer

    message.content.grep(OpenAI::Responses::ResponseOutputText).each do |part|
      count = part.parsed
      case count
      when CrateCount
        puts count.total_crates
      end
    end
  end
end
```

The expected answer is `{"total_crates":43}`. The response object’s `text.format` still reports the original request-level format. After checking for refusals and incomplete responses, parse the answer with the schema from the latest format update.

Each format update replaces the whole format. It stays in effect across turns, including when you update only `reasoning.effort`. To switch back to plain text, append `{"type":"configuration_update","text":{"format":{"type":"text"}}}`. Updates accept `json_schema` and `text` only.

If you replay history manually, keep each update in its original position. After explicit compaction, restate each setting you changed. See [configuration update compatibility](https://developers.openai.com/api/docs/guides/reasoning?api-mode=responses#change-reasoning-mid-conversation).

### Refusals with Structured Outputs

When using Structured Outputs with user-generated input, OpenAI models may occasionally refuse to fulfill the request for safety reasons. Since a refusal does not necessarily follow the schema you have supplied in `response_format`, the API response will include a new field called `refusal` to indicate that the model refused to fulfill the request.

When the `refusal` property appears in your output object, you might present the refusal in your UI, or include conditional logic in code that consumes the response to handle the case of a refused request.

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31const Step = z.object({
  explanation: z.string(),
  output: z.string(),
});

const MathReasoning = z.object({
  steps: z.array(Step),
  final_answer: z.string(),
});

const completion = await openai.chat.completions.parse({
  model: "gpt-6-astra",
  messages: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  response_format: zodResponseFormat(MathReasoning, "math_reasoning"),
});

const math_reasoning = completion.choices[0].message;

// If the model refuses to respond, you will get a refusal message
if (math_reasoning.refusal) {
  console.log(math_reasoning.refusal);
} else {
  console.log(math_reasoning.parsed);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

completion = client.chat.completions.parse(
    model="gpt-6-astra",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format=MathReasoning,
)

math_reasoning = completion.choices[0].message

# If the model refuses to respond, you will get a refusal message

if math_reasoning.refusal:
    print(math_reasoning.refusal)
else:
    print(math_reasoning.parsed)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful math tutor. Guide the user through the solution step by step."),
			openai.UserMessage("how can I solve 8x + 7 = -23"),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
				Name: "math_reasoning", Schema: mathSchema(), Strict: openai.Bool(true),
			}},
		},
	})
	if err != nil {
		panic(err)
	}

	message := completion.Choices[0].Message
	if message.Refusal != "" {
		fmt.Println(message.Refusal)
		return
	}
	fmt.Println(message.Content)
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps",
                Map.of(
                    "type",
                    "array",
                    "items",
                    Map.of(
                        "type",
                        "object",
                        "properties",
                        Map.of(
                            "explanation", Map.of("type", "string"),
                            "output", Map.of("type", "string")),
                        "required",
                        List.of("explanation", "output"),
                        "additionalProperties",
                        false)),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage(
            "You are a helpful math tutor. Guide the user through the solution step by step.")
        .addUserMessage("How can I solve 8x + 7 = -23?")
        .putAdditionalBodyProperty(
            "response_format",
            JsonValue.from(
                Map.of(
                    "type",
                    "json_schema",
                    "json_schema",
                    Map.of("name", "math_reasoning", "strict", true, "schema", schema))))
        .build();

var message = client.chat().completions().create(params).choices().get(0).message();
System.out.println(message.refusal().or(() -> message.content()).orElseThrow());
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        "math_response",
        schema,
        jsonSchemaIsStrict: true
    ),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful math tutor. Guide the user through the solution step by step."), new UserChatMessage("How can I solve 8x + 7 = -23?")],
    options
);

if (!string.IsNullOrEmpty(completion.Refusal))
{
    Console.WriteLine(completion.Refusal);
}
else
{
    Console.WriteLine(completion.Content[0].Text);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48require "openai"

client = OpenAI::Client.new
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: {
        type: :object,
        properties: {
          explanation: { type: :string },
          output: { type: :string }
        },
        required: %w[explanation output],
        additionalProperties: false
      }
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  response_format: {
    type: :json_schema,
    json_schema: {
      name: "math_reasoning",
      strict: true,
      schema: math_schema
    }
  }
)

message = completion.choices.fetch(0).message
puts(message.refusal || message.content)
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44const Step = z.object({
  explanation: z.string(),
  output: z.string(),
});

const MathReasoning = z.object({
  steps: z.array(Step),
  final_answer: z.string(),
});

const response = await openai.responses.parse({
  model: "gpt-6-astra",
  input: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  text: {
    format: zodTextFormat(MathReasoning, "math_response"),
  },
});

for (const output of response.output) {
  if (output.type !== "message") {
    continue;
  }

  for (const item of output.content) {
    if (item.type == "refusal") {
      // If the model refuses to respond, you will get a refusal message
      console.log(item.refusal);
      continue;
    }

    if (!item.parsed) {
      throw new Error("Could not parse response");
    }

    console.log(item.parsed);
  }
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

response = client.responses.parse(
    model="gpt-6-astra",
    input=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    text_format=MathReasoning,
)

for output in response.output:
    if output.type != "message":
        continue

    for item in output.content:
        if item.type == "refusal":
            # If the model refuses to respond, you will get a refusal message
            print(item.refusal)
            continue

        if not item.parsed:
            raise Exception("Could not parse response")

        print(item.parsed)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
)

func main() {
	client := openai.NewClient()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful math tutor. Guide the user through the solution step by step.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("how can I solve 8x + 7 = -23")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONSchema: &responses.ResponseFormatTextJSONSchemaConfigParam{Name: "math_response", Schema: mathSchema(), Strict: openai.Bool(true)},
		}},
	})
	if err != nil {
		panic(err)
	}

	for _, output := range response.Output {
		if output.Type != "message" {
			continue
		}
		for _, content := range output.AsMessage().Content {
			if content.Type == "refusal" {
				fmt.Println(content.AsRefusal().Refusal)
				continue
			}
			fmt.Println(content.AsOutputText().Text)
		}
	}
}

func mathSchema() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"steps":        map[string]any{"type": "array", "items": map[string]any{"type": "object", "properties": map[string]any{"explanation": map[string]any{"type": "string"}, "output": map[string]any{"type": "string"}}, "required": []string{"explanation", "output"}, "additionalProperties": false}},
			"final_answer": map[string]any{"type": "string"},
		},
		"required":             []string{"steps", "final_answer"},
		"additionalProperties": false,
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

Map<String, Object> schema =
    Map.of(
        "type",
        "object",
        "properties",
        Map.of(
            "steps",
                Map.of(
                    "type",
                    "array",
                    "items",
                    Map.of(
                        "type",
                        "object",
                        "properties",
                        Map.of(
                            "explanation", Map.of("type", "string"),
                            "output", Map.of("type", "string")),
                        "required",
                        List.of("explanation", "output"),
                        "additionalProperties",
                        false)),
            "final_answer", Map.of("type", "string")),
        "required",
        List.of("steps", "final_answer"),
        "additionalProperties",
        false);

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content(
                            "You are a helpful math tutor. Guide the user through the solution step by step.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content("How can I solve 8x + 7 = -23?")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("math_reasoning")
                        .strict(true)
                        .schema(
                            JsonValue.from(schema)
                                .convert(ResponseFormatTextJsonSchemaConfig.Schema.class))
                        .build())
                .build())
        .build();

var response = client.responses().create(params);
for (var output : response.output()) {
  if (output.message().isEmpty()) continue;
  for (var content : output.message().orElseThrow().content()) {
    if (content.refusal().isPresent()) {
      System.out.println(content.refusal().orElseThrow().refusal());
    } else {
      content.outputText().ifPresent(text -> System.out.println(text.text()));
    }
  }
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

BinaryData schema = BinaryData.FromString(
    """
    {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "explanation": { "type": "string" },
              "output": { "type": "string" }
            },
            "required": ["explanation", "output"],
            "additionalProperties": false
          }
        },
        "final_answer": { "type": "string" }
      },
      "required": ["steps", "final_answer"],
      "additionalProperties": false
    }
    """
);
CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonSchemaFormat(
            "math_response",
            schema,
            jsonSchemaIsStrict: true
        ),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful math tutor. Guide the user through the solution step by step."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("How can I solve 8x + 7 = -23?"));

ResponseResult response = await client.CreateResponseAsync(options);
foreach (MessageResponseItem message in response.OutputItems.OfType<MessageResponseItem>())
{
    foreach (ResponseContentPart content in message.Content)
    {
        Console.WriteLine(
            content.Kind == ResponseContentPartKind.Refusal ? content.Refusal : content.Text
        );
    }
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58require "openai"

client = OpenAI::Client.new
math_schema = {
  type: :object,
  properties: {
    steps: {
      type: :array,
      items: {
        type: :object,
        properties: {
          explanation: { type: :string },
          output: { type: :string }
        },
        required: %w[explanation output],
        additionalProperties: false
      }
    },
    final_answer: { type: :string }
  },
  required: %w[steps final_answer],
  additionalProperties: false
}

response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful math tutor. Guide the user through the solution step by step."
    },
    {
      role: :user,
      content: "How can I solve 8x + 7 = -23?"
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "math_response",
      strict: true,
      schema: math_schema
    }
  }
)

response.output.each do |item|
  next unless item.is_a?(OpenAI::Models::Responses::ResponseOutputMessage)

  item.content.each do |content|
    case content
    when OpenAI::Models::Responses::ResponseOutputRefusal
      puts(content.refusal)
    when OpenAI::Models::Responses::ResponseOutputText
      puts(content.text)
    end
  end
end
```

The API response from a refusal will look something like this:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28{
  "id": "chatcmpl-9nYAG9LPNonX8DAyrkwYfemr3C8HC",
  "object": "chat.completion",
  "created": 1721596428,
  "model": "gpt-4o-2024-08-06",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "refusal": "I'm sorry, I cannot assist with that request."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 81,
    "completion_tokens": 11,
    "total_tokens": 92,
    "completion_tokens_details": {
      "reasoning_tokens": 0,
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    }
  },
  "system_fingerprint": "fp_3407719c7f"
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32{
  "id": "resp_1234567890",
  "object": "response",
  "created_at": 1721596428,
  "status": "completed",
  "completed_at": 1721596429,
  "error": null,
  "incomplete_details": null,
  "input": [],
  "instructions": null,
  "max_output_tokens": null,
  "model": "gpt-4o-2024-08-06",
  "output": [{
    "id": "msg_1234567890",
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "refusal",
        "refusal": "I'm sorry, I cannot assist with that request."
      }
    ]
  }],
  "usage": {
    "input_tokens": 81,
    "output_tokens": 11,
    "total_tokens": 92,
    "output_tokens_details": {
      "reasoning_tokens": 0,
    }
  },
}
```

### Tips and best practices

#### Handling user-generated input

If your application is using user-generated input, make sure your prompt includes instructions on how to handle situations where the input cannot result in a valid response.

The model will always try to adhere to the provided schema, which can result in hallucinations if the input is completely unrelated to the schema.

You could include language in your prompt to specify that you want to return empty parameters, or a specific sentence, if the model detects that the input is incompatible with the task.

#### Handling mistakes

Structured Outputs can still contain mistakes. If you see mistakes, try adjusting your instructions, providing examples in the system instructions, or splitting tasks into simpler subtasks. Refer to the [prompt engineering guide](https://developers.openai.com/api/docs/guides/prompt-engineering) for more guidance on how to tweak your inputs.

#### Avoid JSON schema divergence

To prevent your JSON Schema and corresponding types in your programming language from diverging, we strongly recommend using native SDK schema helpers where available.

If you prefer to specify the JSON schema directly, you could add CI rules that flag when either the JSON schema or underlying data objects are edited, or add a CI step that automatically generates the JSON Schema from type definitions (or vice-versa).

## Streaming

You can use streaming to process model responses or function call arguments as they are being generated, and parse them as structured data.

That way, you don’t have to wait for the entire response to complete before handling it. This is particularly useful if you would like to display JSON fields one by one, or handle function call arguments as soon as they are available.

We recommend relying on the SDKs to handle streaming with Structured Outputs.

You can find an example of how to stream function call arguments without the SDK `stream` helper in the [function calling guide](https://developers.openai.com/api/docs/guides/function-calling#streaming).

Here is how you can stream a model response with the `stream` helper:

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40import OpenAI from "openai";
import { zodResponseFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI();

const EntitiesSchema = z.object({
  attributes: z.array(z.string()),
  colors: z.array(z.string()),
  animals: z.array(z.string()),
});

const stream = openai.chat.completions
  .stream({
    model: "gpt-6-astra",
    messages: [
      { role: "system", content: "Extract entities from the input text" },
      {
        role: "user",
        content:
          "The quick brown fox jumps over the lazy dog with piercing blue eyes",
      },
    ],
    response_format: zodResponseFormat(EntitiesSchema, "entities"),
  })
  .on("refusal.done", () => console.log("request refused"))
  .on("content.delta", ({ snapshot, parsed }) => {
    console.log("content:", snapshot);
    console.log("parsed:", parsed);
    console.log();
  })
  .on("content.done", (props) => {
    console.log(props);
  });

await stream.done();

const finalCompletion = await stream.finalChatCompletion();

console.log(finalCompletion);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34from pydantic import BaseModel
from openai import OpenAI

class EntitiesModel(BaseModel):
    attributes: list[str]
    colors: list[str]
    animals: list[str]

client = OpenAI()

with client.beta.chat.completions.stream(
    model="gpt-6-astra",
    messages=[
        {"role": "system", "content": "Extract entities from the input text"},
        {
            "role": "user",
            "content": "The quick brown fox jumps over the lazy dog with piercing blue eyes",
        },
    ],
    response_format=EntitiesModel,
) as stream:
    for event in stream:
        if event.type == "content.delta":
            if event.parsed is not None:  # Print the parsed data as JSON
                print("content.delta parsed:", event.parsed)
        elif event.type == "content.done":
            print("content.done")
        elif event.type == "error":
            print("Error in stream:", event.error)

final_completion = stream.get_final_completion()
print("Final completion:", final_completion)
```

You can also use the `stream` helper to parse function call arguments:

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38import { zodFunction } from "openai/helpers/zod";
import OpenAI from "openai/index";
import { z } from "zod";

const GetWeatherArgs = z.object({
  city: z.string(),
  country: z.string(),
});

const client = new OpenAI();

const stream = client.chat.completions
  .stream({
    model: "gpt-5.6-terra",
    reasoning_effort: "none",
    parallel_tool_calls: true,
    messages: [
      {
        role: "user",
        content: "What's the weather like in SF and London?",
      },
    ],
    tools: [zodFunction({ name: "get_weather", parameters: GetWeatherArgs })],
  })
  .on("tool_calls.function.arguments.delta", (props) =>
    console.log("tool_calls.function.arguments.delta", props)
  )
  .on("tool_calls.function.arguments.done", (props) =>
    console.log("tool_calls.function.arguments.done", props)
  )
  .on("refusal.delta", ({ delta }) => {
    process.stdout.write(delta);
  })
  .on("refusal.done", () => console.log("request refused"));

const completion = await stream.finalChatCompletion();

console.log("final completion:", completion);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34from pydantic import BaseModel
import openai
from openai import OpenAI

class GetWeather(BaseModel):
    city: str
    country: str

client = OpenAI()

with client.beta.chat.completions.stream(
    model="gpt-5.6-terra",
    reasoning_effort="none",
    messages=[
        {
            "role": "user",
            "content": "What's the weather like in SF and London?",
        },
    ],
    tools=[
        openai.pydantic_function_tool(GetWeather, name="get_weather"),
    ],
    parallel_tool_calls=True,
) as stream:
    for event in stream:
        if (
            event.type == "tool_calls.function.arguments.delta"
            or event.type == "tool_calls.function.arguments.done"
        ):
            print(event)

print(stream.get_final_completion())
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37import { OpenAI } from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const EntitiesSchema = z.object({
  attributes: z.array(z.string()),
  colors: z.array(z.string()),
  animals: z.array(z.string()),
});

const openai = new OpenAI();
const stream = openai.responses
  .stream({
    model: "gpt-6-astra",
    input: [
      { role: "user", content: "What's the weather like in Paris today?" },
    ],
    text: {
      format: zodTextFormat(EntitiesSchema, "entities"),
    },
  })
  .on("response.refusal.delta", (event) => {
    process.stdout.write(event.delta);
  })
  .on("response.output_text.delta", (event) => {
    process.stdout.write(event.delta);
  })
  .on("response.output_text.done", () => {
    process.stdout.write("\n");
  })
  .on("error", (error) => {
    console.error(error);
  });

const result = await stream.finalResponse();

console.log(result);
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35from openai import OpenAI
from pydantic import BaseModel

class EntitiesModel(BaseModel):
    attributes: list[str]
    colors: list[str]
    animals: list[str]

client = OpenAI()

with client.responses.stream(
    model="gpt-6-astra",
    input=[
        {"role": "system", "content": "Extract entities from the input text"},
        {
            "role": "user",
            "content": "The quick brown fox jumps over the lazy dog with piercing blue eyes",
        },
    ],
    text_format=EntitiesModel,
) as stream:
    for event in stream:
        if event.type == "response.refusal.delta":
            print(event.delta, end="")
        elif event.type == "response.output_text.delta":
            print(event.delta, end="")
        elif event.type == "response.error":
            print(event.error, end="")
        elif event.type == "response.completed":
            print("Completed")  # print(event.response.output)

    final_response = stream.get_final_response()
    print(final_response)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.core.http.StreamResponse;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseFormatTextJsonSchemaConfig;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseStreamEvent;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;
import java.util.Map;

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content("Extract entities from the input text")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content(
                            "The quick brown fox jumps over the lazy dog with piercing blue eyes")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(
                    ResponseFormatTextJsonSchemaConfig.builder()
                        .name("entities")
                        .strict(true)
                        .schema(
                            ResponseFormatTextJsonSchemaConfig.Schema.builder()
                                .putAdditionalProperty("type", JsonValue.from("object"))
                                .putAdditionalProperty(
                                    "properties",
                                    JsonValue.from(
                                        Map.of(
                                            "attributes",
                                            Map.of(
                                                "type",
                                                "array",
                                                "items",
                                                Map.of("type", "string")),
                                            "colors",
                                            Map.of(
                                                "type",
                                                "array",
                                                "items",
                                                Map.of("type", "string")),
                                            "animals",
                                            Map.of(
                                                "type",
                                                "array",
                                                "items",
                                                Map.of("type", "string")))))
                                .putAdditionalProperty(
                                    "required",
                                    JsonValue.from(List.of("attributes", "colors", "animals")))
                                .putAdditionalProperty(
                                    "additionalProperties", JsonValue.from(false))
                                .build())
                        .build())
                .build())
        .build();

try (StreamResponse<ResponseStreamEvent> stream = client.responses().createStreaming(params)) {
  stream.stream()
      .forEach(
          event -> {
            event.outputTextDelta().ifPresent(delta -> System.out.print(delta.delta()));
            event.refusalDelta().ifPresent(refusal -> System.out.print(refusal.delta()));
            event.error().ifPresent(error -> System.out.println(error.message()));
            event
                .completed()
                .ifPresent(
                    completed -> {
                      System.out.println("Completed");
                      System.out.println(completed.response());
                    });
          });
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56require "openai"

client = OpenAI::Client.new
entities_schema = {
  type: :object,
  properties: {
    attributes: {
      type: :array,
      items: { type: :string }
    },
    colors: {
      type: :array,
      items: { type: :string }
    },
    animals: {
      type: :array,
      items: { type: :string }
    }
  },
  required: %w[attributes colors animals],
  additionalProperties: false
}

stream = client.responses.stream(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "Extract entities from the input text."
    },
    {
      role: :user,
      content: "The quick brown fox jumps over the lazy dog with piercing blue eyes."
    }
  ],
  text: {
    format: {
      type: :json_schema,
      name: "entities",
      strict: true,
      schema: entities_schema
    }
  }
)

stream.each do |event|
  case event
  when OpenAI::Models::Responses::ResponseRefusalDeltaEvent,
       OpenAI::Models::Responses::ResponseTextDeltaEvent
    print(event.delta)
  when OpenAI::Models::Responses::ResponseErrorEvent
    warn(event.message)
  when OpenAI::Models::Responses::ResponseCompletedEvent
    puts("\nCompleted")
  end
end
```

## Supported schemas

Structured Outputs supports a subset of the [JSON Schema](https://json-schema.org/docs) language.

#### Supported types

The following types are supported for Structured Outputs:

*   String
*   Number
*   Boolean
*   Integer
*   Object
*   Array
*   Enum
*   anyOf

#### Supported properties

In addition to specifying the type of a property, you can specify a selection of additional constraints:

**Supported `string` properties:**

*   `pattern` — A regular expression that the string must match.
*   `format` — Predefined formats for strings. Currently supported: 
    *   `date-time`
    *   `time`
    *   `date`
    *   `duration`
    *   `email`
    *   `hostname`
    *   `ipv4`
    *   `ipv6`
    *   `uuid`

**Supported `number` properties:**

*   `multipleOf` — The number must be a multiple of this value.
*   `maximum` — The number must be less than or equal to this value.
*   `exclusiveMaximum` — The number must be less than this value.
*   `minimum` — The number must be greater than or equal to this value.
*   `exclusiveMinimum` — The number must be greater than this value.

**Supported `array` properties:**

*   `minItems` — The array must have at least this many items.
*   `maxItems` — The array must have at most this many items.

Here are some examples on how you can use these type restrictions:

String Restrictions Number Restrictions

String Restrictions

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27{
    "name": "user_data",
    "strict": true,
    "schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the user"
            },
            "username": {
                "type": "string",
                "description": "The username of the user. Must start with @",
                "pattern": "^@[a-zA-Z0-9_]+$"
            },
            "email": {
                "type": "string",
                "description": "The email of the user",
                "format": "email"
            }
        },
        "additionalProperties": false,
        "required": [
            "name", "username", "email"
        ]
    }
}
```

Number Restrictions

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28{
    "name": "weather_data",
    "strict": true,
    "schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get the weather for"
            },
            "unit": {
                "type": ["string", "null"],
                "description": "The unit to return the temperature in",
                "enum": ["F", "C"]
            },
            "value": {
                "type": "number",
                "description": "The actual temperature value in the location",
                "minimum": -130,
                "maximum": 130
            }
        },
        "additionalProperties": false,
        "required": [
            "location", "unit", "value"
        ]
    }
}
```

Note these constraints are [not yet supported for fine-tuned models](https://developers.openai.com/api/docs/guides/structured-outputs#some-type-specific-keywords-are-not-yet-supported).

#### Root objects must not be `anyOf` and must be an object

Note that the root level object of a schema must be an object, and not use `anyOf`. A pattern that appears in Zod (as one example) is using a discriminated union, which produces an `anyOf` at the top level. So code such as the following won’t work:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17import { z } from "zod";
import { zodResponseFormat } from "openai/helpers/zod";

const BaseResponseSchema = z.object({
  /* ... */
});
const UnsuccessfulResponseSchema = z.object({
  /* ... */
});

const finalSchema = z.discriminatedUnion("status", [
  BaseResponseSchema,
  UnsuccessfulResponseSchema,
]);

// Invalid JSON Schema for Structured Outputs
const json = zodResponseFormat(finalSchema, "final_schema");
```

#### All fields must be `required`

To use Structured Outputs, all fields or function parameters must be specified as `required`.

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21{
    "name": "get_weather",
    "description": "Fetches the weather in the given location",
    "strict": true,
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get the weather for"
            },
            "unit": {
                "type": "string",
                "description": "The unit to return the temperature in",
                "enum": ["F", "C"]
            }
        },
        "additionalProperties": false,
        "required": ["location", "unit"]
    }
}
```

Although all fields must be required (and the model will return a value for each parameter), it is possible to emulate an optional parameter by using a union type with `null`.

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23{
    "name": "get_weather",
    "description": "Fetches the weather in the given location",
    "strict": true,
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get the weather for"
            },
            "unit": {
                "type": ["string", "null"],
                "description": "The unit to return the temperature in",
                "enum": ["F", "C"]
            }
        },
        "additionalProperties": false,
        "required": [
            "location", "unit"
        ]
    }
}
```

#### Objects have limitations on nesting depth and size

A schema may have up to 5000 object properties total, with up to 10 levels of nesting.

#### Limitations on total string size

In a schema, total string length of all property names, definition names, enum values, and const values cannot exceed 120,000 characters.

#### Limitations on enum size

A schema may have up to 1000 enum values across all enum properties.

For a single enum property with string values, the total string length of all enum values cannot exceed 15,000 characters when there are more than 250 enum values.

#### `additionalProperties: false` must always be set in objects

`additionalProperties` controls whether it is allowable for an object to contain additional keys / values that were not defined in the JSON Schema.

Structured Outputs only supports generating specified keys / values, so we require developers to set `additionalProperties: false` to opt into Structured Outputs.

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23{
    "name": "get_weather",
    "description": "Fetches the weather in the given location",
    "strict": true,
    "schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get the weather for"
            },
            "unit": {
                "type": "string",
                "description": "The unit to return the temperature in",
                "enum": ["F", "C"]
            }
        },
        "additionalProperties": false,
        "required": [
            "location", "unit"
        ]
    }
}
```

#### Key ordering

When using Structured Outputs, outputs will be produced in the same order as the ordering of keys in the schema.

#### Some type-specific keywords are not yet supported

*   **Composition:**`allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, `else`

For fine-tuned models, we additionally do not support the following:

*   **For strings:**`minLength`, `maxLength`, `pattern`, `format`
*   **For numbers:**`minimum`, `maximum`, `multipleOf`
*   **For objects:**`patternProperties`
*   **For arrays:**`minItems`, `maxItems`

If you turn on Structured Outputs by supplying `strict: true` and call the API with an unsupported JSON Schema, you will receive an error.

#### For `anyOf`, the nested schemas must each be a valid JSON Schema per this subset

Here’s an example supported anyOf schema:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56{
    "type": "object",
    "properties": {
        "item": {
            "anyOf": [
                {
                    "type": "object",
                    "description": "The user object to insert into the database",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the user"
                        },
                        "age": {
                            "type": "number",
                            "description": "The age of the user"
                        }
                    },
                    "additionalProperties": false,
                    "required": [
                        "name",
                        "age"
                    ]
                },
                {
                    "type": "object",
                    "description": "The address object to insert into the database",
                    "properties": {
                        "number": {
                            "type": "string",
                            "description": "The number of the address. Eg. for 123 main st, this would be 123"
                        },
                        "street": {
                            "type": "string",
                            "description": "The street name. Eg. for 123 main st, this would be main st"
                        },
                        "city": {
                            "type": "string",
                            "description": "The city of the address"
                        }
                    },
                    "additionalProperties": false,
                    "required": [
                        "number",
                        "street",
                        "city"
                    ]
                }
            ]
        }
    },
    "additionalProperties": false,
    "required": [
        "item"
    ]
}
```

#### Definitions are supported

You can use definitions to define subschemas which are referenced throughout your schema. The following is a simple example.

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37{
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "$ref": "#/$defs/step"
            }
        },
        "final_answer": {
            "type": "string"
        }
    },
    "$defs": {
        "step": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string"
                },
                "output": {
                    "type": "string"
                }
            },
            "required": [
                "explanation",
                "output"
            ],
            "additionalProperties": false
        }
    },
    "required": [
        "steps",
        "final_answer"
    ],
    "additionalProperties": false
}
```

#### Recursive schemas are supported

Sample recursive schema using `#` to indicate root recursion.

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47{
    "name": "ui",
    "description": "Dynamically generated UI",
    "strict": true,
    "schema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "The type of the UI component",
                "enum": ["div", "button", "header", "section", "field", "form"]
            },
            "label": {
                "type": "string",
                "description": "The label of the UI component, used for buttons or form fields"
            },
            "children": {
                "type": "array",
                "description": "Nested UI components",
                "items": {
                    "$ref": "#"
                }
            },
            "attributes": {
                "type": "array",
                "description": "Arbitrary attributes for the UI component, suitable for any element",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the attribute, for example onClick or className"
                        },
                        "value": {
                            "type": "string",
                            "description": "The value of the attribute"
                        }
                    },
                    "additionalProperties": false,
                    "required": ["name", "value"]
                }
            }
        },
        "required": ["type", "label", "children", "attributes"],
        "additionalProperties": false
    }
}
```

Sample recursive schema using explicit recursion:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37{
    "type": "object",
    "properties": {
        "linked_list": {
            "$ref": "#/$defs/linked_list_node"
        }
    },
    "$defs": {
        "linked_list_node": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number"
                },
                "next": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/linked_list_node"
                        },
                        {
                            "type": "null"
                        }
                    ]
                }
            },
            "additionalProperties": false,
            "required": [
                "next",
                "value"
            ]
        }
    },
    "additionalProperties": false,
    "required": [
        "linked_list"
    ]
}
```

## JSON mode

JSON mode is a more basic version of the Structured Outputs feature. While JSON mode ensures that model output is valid JSON, Structured Outputs reliably matches the model’s output to the schema you specify. We recommend you use Structured Outputs if it is supported for your use case.

When JSON mode is turned on, the model’s output is ensured to be valid JSON, except for in some edge cases that you should detect and handle appropriately.

To turn on JSON mode with the Chat Completions, set the `response_format` to `{ "type": "json_object" }`. If you are using function calling, JSON mode is always turned on.

To turn on JSON mode with the Responses API you can set the `text.format` to `{ "type": "json_object" }`. If you are using function calling, JSON mode is always turned on.

Important notes:

*   When using JSON mode, you must always instruct the model to produce JSON via some message in the conversation, for example via your system message. If you don’t include an explicit instruction to generate JSON, the model may generate an unending stream of whitespace and the request may run continually until it reaches the token limit. To help ensure you don’t forget, the API will throw an error if the string “JSON” does not appear somewhere in the context.
*   JSON mode will not guarantee the output matches any specific schema, only that it is valid and parses without errors. You should use Structured Outputs to ensure it matches your schema, or if that is not possible, you should use a validation library and potentially retries to ensure that the output matches your desired schema.
*   Your application must detect and handle the edge cases that can result in the model output not being a complete JSON object (see below)

Handling edge cases

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52const we_did_not_specify_stop_tokens = true;

try {
  const response = await openai.chat.completions.create({
    model: "gpt-6-astra",
    messages: [
      {
        role: "system",
        content: "You are a helpful assistant designed to output JSON.",
      },
      {
        role: "user",
        content:
          "Who won the world series in 2020? Please respond in the format {winner: ...}",
      },
    ],
    store: true,
    response_format: { type: "json_object" },
  });

  // Check if the conversation was too long for the context window, resulting in incomplete JSON
  if (response.choices[0].finish_reason === "length") {
    // your code should handle this error case
  }

  // Check if the OpenAI safety system refused the request and generated a refusal instead
  if (response.choices[0].message.refusal) {
    // your code should handle this error case
    // In this case, the .content field will contain the explanation (if any) that the model generated for why it is refusing
    console.log(response.choices[0].message.refusal);
  }

  // Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
  if (response.choices[0].finish_reason === "content_filter") {
    // your code should handle this error case
  }

  if (response.choices[0].finish_reason === "stop") {
    // In this case the model has either successfully finished generating the JSON object according to your schema, or the model generated one of the tokens you provided as a "stop token"

    if (we_did_not_specify_stop_tokens) {
      // If you didn't specify any stop tokens, then the generation is complete and the content key will contain the serialized JSON object
      // This will parse successfully and should now contain  {"winner": "Los Angeles Dodgers"}
      console.log(JSON.parse(response.choices[0].message.content));
    } else {
      // Check if the response.choices[0].message.content ends with one of your stop tokens and handle appropriately
    }
  }
} catch (e) {
  // Your code should handle errors here, for example a network error calling the API
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42we_did_not_specify_stop_tokens = True

try:
    response = client.chat.completions.create(
        model="gpt-6-astra",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON.",
            },
            {
                "role": "user",
                "content": 'Who won the World Series in 2020? Respond as {"winner": "team name"}.',
            },
        ],
        response_format={"type": "json_object"},
    )

    # Check if the conversation was too long for the context window, resulting in incomplete JSON
    if response.choices[0].finish_reason == "length":
        raise RuntimeError("The response was truncated before the JSON completed.")

    # Check if the OpenAI safety system refused the request and generated a refusal instead
    if response.choices[0].message.refusal:
        # your code should handle this error case
        # In this case, the .content field will contain the explanation (if any) that the model generated for why it is refusing
        print(response.choices[0].message.refusal)

    # Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
    if response.choices[0].finish_reason == "content_filter":
        raise RuntimeError("The response was interrupted by the content filter.")

    if response.choices[0].finish_reason == "stop":
        # In this case the model has either successfully finished generating the JSON object according to your schema, or the model generated one of the tokens you provided as a "stop token"

        if we_did_not_specify_stop_tokens:
            # If you didn't specify any stop tokens, then the generation is complete and the content key will contain the serialized JSON object
            # This will parse successfully and should now contain  "{"winner": "Los Angeles Dodgers"}"
            print(response.choices[0].message.content)
except Exception as e:
    # Your code should handle errors here, for example a network error calling the API
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	completion, err := client.Chat.Completions.New(context.Background(), openai.ChatCompletionNewParams{
		Model: "gpt-6-astra",
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage("You are a helpful assistant designed to output JSON."),
			openai.UserMessage("Who won the world series in 2020? Please respond in the format {winner: ...}"),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONObject: &shared.ResponseFormatJSONObjectParam{},
		},
	})
	if err != nil {
		panic(err)
	}

	choice := completion.Choices[0]
	if choice.FinishReason == "length" || choice.FinishReason == "content_filter" {
		fmt.Println("The JSON response is incomplete.")
		return
	}
	if choice.Message.Refusal != "" {
		fmt.Println(choice.Message.Refusal)
		return
	}
	if choice.FinishReason == "stop" {
		var value map[string]any
		if err := json.Unmarshal([]byte(choice.Message.Content), &value); err != nil {
			panic(err)
		}
		fmt.Println(value)
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31import com.fasterxml.jackson.databind.ObjectMapper;
import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import java.io.IOException;
import java.util.Map;

ChatCompletionCreateParams params =
    ChatCompletionCreateParams.builder()
        .model("gpt-6-astra")
        .addSystemMessage("You are a helpful assistant designed to output JSON.")
        .addUserMessage("Who won the World Series in 2020? Respond as {winner: ...}.")
        .putAdditionalBodyProperty(
            "response_format", JsonValue.from(Map.of("type", "json_object")))
        .build();

var choice = client.chat().completions().create(params).choices().get(0);
if (choice.finishReason().equals(ChatCompletion.Choice.FinishReason.LENGTH)
    || choice.finishReason().equals(ChatCompletion.Choice.FinishReason.CONTENT_FILTER)) {
  System.out.println("The JSON response is incomplete.");
} else if (choice.message().refusal().isPresent()) {
  System.out.println(choice.message().refusal().orElseThrow());
} else if (choice.finishReason().equals(ChatCompletion.Choice.FinishReason.STOP)) {
  String content = choice.message().content().orElseThrow();
  System.out.println(
      new ObjectMapper()
          .writerWithDefaultPrettyPrinter()
          .writeValueAsString(new ObjectMapper().readTree(content)));
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35using OpenAI.Chat;

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
string model = "gpt-6-astra";
ChatClient client = new(model, key);

ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonObjectFormat(),
};
ChatCompletion completion = await client.CompleteChatAsync(
    [new SystemChatMessage("You are a helpful assistant designed to output JSON."), new UserChatMessage("Who won the World Series in 2020? Respond with the winner in JSON.")],
    options
);

if (completion.FinishReason == ChatFinishReason.Length)
{
    Console.WriteLine("The response was truncated before the JSON completed.");
}
else if (completion.FinishReason == ChatFinishReason.ContentFilter)
{
    Console.WriteLine("The response was interrupted by the content filter.");
}
else if (!string.IsNullOrEmpty(completion.Refusal))
{
    Console.WriteLine(completion.Refusal);
}
else if (completion.FinishReason == ChatFinishReason.Stop && completion.Content.Count > 0)
{
    Console.WriteLine(completion.Content[0].Text);
}
else
{
    throw new InvalidOperationException("The completion did not contain a JSON response.");
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32require "json"
require "openai"

client = OpenAI::Client.new
completion = client.chat.completions.create(
  model: "gpt-6-astra",
  messages: [
    {
      role: :system,
      content: "You are a helpful assistant designed to output JSON."
    },
    {
      role: :user,
      content: "Who won the World Series in 2020? Respond in the format {winner: ...}."
    }
  ],
  response_format: { type: :json_object }
)

choice = completion.choices.fetch(0)
finish_reason = choice.finish_reason
if [
  OpenAI::Chat::ChatCompletion::Choice::FinishReason::LENGTH,
  OpenAI::Chat::ChatCompletion::Choice::FinishReason::CONTENT_FILTER
].include?(finish_reason)
  warn("The JSON response is incomplete.")
elsif choice.message.refusal
  puts(choice.message.refusal)
elsif finish_reason == OpenAI::Chat::ChatCompletion::Choice::FinishReason::STOP
  content = choice.message.content or raise "No response content"
  puts(JSON.pretty_generate(JSON.parse(content)))
end
```

Python

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60const we_did_not_specify_stop_tokens = true;

try {
  const response = await openai.responses.create({
    model: "gpt-6-astra",
    input: [
      {
        role: "system",
        content: "You are a helpful assistant designed to output JSON.",
      },
      {
        role: "user",
        content:
          "Who won the world series in 2020? Please respond in the format {winner: ...}",
      },
    ],
    text: { format: { type: "json_object" } },
  });

  const message = response.output.find((item) => item.type === "message");
  const messageContent = message?.content[0];

  // Check if the conversation was too long for the context window, resulting in incomplete JSON
  if (
    response.status === "incomplete" &&
    response.incomplete_details.reason === "max_output_tokens"
  ) {
    // your code should handle this error case
  }

  // Check if the OpenAI safety system refused the request and generated a refusal instead
  if (messageContent?.type === "refusal") {
    // your code should handle this error case
    // In this case, the .content field will contain the explanation (if any) that the model generated for why it is refusing
    console.log(messageContent.refusal);
  }

  // Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
  if (
    response.status === "incomplete" &&
    response.incomplete_details.reason === "content_filter"
  ) {
    // your code should handle this error case
  }

  if (response.status === "completed") {
    // In this case the model has either successfully finished generating the JSON object according to your schema, or the model generated one of the tokens you provided as a "stop token"

    if (we_did_not_specify_stop_tokens) {
      // If you didn't specify any stop tokens, then the generation is complete and the content key will contain the serialized JSON object
      // This will parse successfully and should now contain  {"winner": "Los Angeles Dodgers"}
      console.log(JSON.parse(response.output_text));
    } else {
      // Check if the response.output_text ends with one of your stop tokens and handle appropriately
    }
  }
} catch (e) {
  // Your code should handle errors here, for example a network error calling the API
  console.error(e);
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51we_did_not_specify_stop_tokens = True

try:
    response = client.responses.create(
        model="gpt-6-astra",
        input=[
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON.",
            },
            {
                "role": "user",
                "content": 'Who won the World Series in 2020? Respond as {"winner": "team name"}.',
            },
        ],
        text={"format": {"type": "json_object"}},
    )

    message = next((item for item in response.output if item.type == "message"), None)
    message_content = message.content[0] if message and message.content else None

    # Check if the conversation was too long for the context window, resulting in incomplete JSON
    if (
        response.status == "incomplete"
        and response.incomplete_details.reason == "max_output_tokens"
    ):
        raise RuntimeError("The response was truncated before the JSON completed.")

    # Check if the OpenAI safety system refused the request and generated a refusal instead
    if message_content and message_content.type == "refusal":
        # your code should handle this error case
        # In this case, the .content field will contain the explanation (if any) that the model generated for why it is refusing
        print(message_content.refusal)

    # Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
    if (
        response.status == "incomplete"
        and response.incomplete_details.reason == "content_filter"
    ):
        raise RuntimeError("The response was interrupted by the content filter.")

    if response.status == "completed":
        # In this case the model has either successfully finished generating the JSON object according to your schema, or the model generated one of the tokens you provided as a "stop token"

        if we_did_not_specify_stop_tokens:
            # If you didn't specify any stop tokens, then the generation is complete and the content key will contain the serialized JSON object
            # This will parse successfully and should now contain  "{"winner": "Los Angeles Dodgers"}"
            print(response.output_text)
except Exception as e:
    # Your code should handle errors here, for example a network error calling the API
    print(e)
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/responses"
	"github.com/openai/openai-go/v3/shared"
)

func main() {
	client := openai.NewClient()
	response, err := client.Responses.New(context.Background(), responses.ResponseNewParams{
		Model: "gpt-6-astra",
		Input: responses.ResponseNewParamsInputUnion{OfInputItemList: responses.ResponseInputParam{
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("You are a helpful assistant designed to output JSON.")},
				responses.EasyInputMessageRoleSystem,
			),
			responses.ResponseInputItemParamOfMessage(
				responses.ResponseInputMessageContentListParam{responses.ResponseInputContentParamOfInputText("Who won the world series in 2020? Please respond in the format {winner: ...}")},
				responses.EasyInputMessageRoleUser,
			),
		}},
		Text: responses.ResponseTextConfigParam{Format: responses.ResponseFormatTextConfigUnionParam{
			OfJSONObject: &shared.ResponseFormatJSONObjectParam{},
		}},
	})
	if err != nil {
		panic(err)
	}

	if response.Status == "incomplete" {
		fmt.Println("The JSON response is incomplete.")
		return
	}
	for _, output := range response.Output {
		if output.Type != "message" {
			continue
		}
		for _, content := range output.AsMessage().Content {
			if content.Type == "refusal" {
				fmt.Println(content.AsRefusal().Refusal)
				return
			}
		}
	}
	if response.Status == "completed" {
		var value map[string]any
		if err := json.Unmarshal([]byte(response.OutputText()), &value); err != nil {
			panic(err)
		}
		fmt.Println(value)
	}
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.errors.OpenAIServiceException;
import com.openai.models.ResponseFormatJsonObject;
import com.openai.models.responses.EasyInputMessage;
import com.openai.models.responses.ResponseCreateParams;
import com.openai.models.responses.ResponseInputItem;
import com.openai.models.responses.ResponseStatus;
import com.openai.models.responses.ResponseTextConfig;
import java.util.List;

ResponseCreateParams params =
    ResponseCreateParams.builder()
        .model("gpt-6-astra")
        .inputOfResponse(
            List.of(
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.SYSTEM)
                        .content("You are a helpful assistant designed to output JSON.")
                        .build()),
                ResponseInputItem.ofEasyInputMessage(
                    EasyInputMessage.builder()
                        .role(EasyInputMessage.Role.USER)
                        .content(
                            "Who won the World Series in 2020? Respond in the format {winner: ...}.")
                        .build())))
        .text(
            ResponseTextConfig.builder()
                .format(ResponseFormatJsonObject.builder().build())
                .build())
        .build();

try {
  var response = client.responses().create(params);
  if (response.status().filter(ResponseStatus.INCOMPLETE::equals).isPresent()) {
    String reason =
        response
            .incompleteDetails()
            .flatMap(details -> details.reason())
            .map(Object::toString)
            .orElse("unknown");
    System.out.println("The JSON response is incomplete. Reason: " + reason);
    return;
  }

  for (var output : response.output()) {
    if (output.message().isEmpty()) continue;
    for (var content : output.message().orElseThrow().content()) {
      if (content.refusal().isPresent()) {
        System.out.println(content.refusal().orElseThrow().refusal());
        return;
      }
      if (response.status().filter(ResponseStatus.COMPLETED::equals).isPresent()) {
        content.outputText().ifPresent(text -> System.out.println(text.text()));
      }
    }
  }
} catch (OpenAIServiceException error) {
  System.out.println("Request failed: " + error.getMessage());
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46using OpenAI.Responses;
#pragma warning disable OPENAI001

string key = Environment.GetEnvironmentVariable("OPENAI_API_KEY")!;
ResponsesClient client = new(key);

CreateResponseOptions options = new()
{
    Model = "gpt-6-astra",
    TextOptions = new ResponseTextOptions
    {
        TextFormat = ResponseTextFormat.CreateJsonObjectFormat(),
    },
};
options.InputItems.Add(ResponseItem.CreateSystemMessageItem("You are a helpful assistant designed to output JSON."));
options.InputItems.Add(ResponseItem.CreateUserMessageItem("Who won the World Series in 2020? Respond with the winner in JSON."));

ResponseResult response = await client.CreateResponseAsync(options);
if (
    response.Status == ResponseStatus.Incomplete
    && response.IncompleteStatusDetails?.Reason == ResponseIncompleteStatusReason.MaxOutputTokens
)
{
    Console.WriteLine("The response was truncated before the JSON completed.");
}
else if (
    response.Status == ResponseStatus.Incomplete
    && response.IncompleteStatusDetails?.Reason == ResponseIncompleteStatusReason.ContentFilter
)
{
    Console.WriteLine("The response was interrupted by the content filter.");
}
else if (response.Status == ResponseStatus.Completed)
{
    MessageResponseItem message = response.OutputItems.OfType<MessageResponseItem>().FirstOrDefault()
        ?? throw new InvalidOperationException("The response did not include an output message.");
    ResponseContentPart content = message.Content.FirstOrDefault()
        ?? throw new InvalidOperationException("The response did not include output content.");
    Console.WriteLine(
        content.Kind == ResponseContentPartKind.Refusal ? content.Refusal : content.Text
    );
}
else
{
    throw new InvalidOperationException($"The response ended with status: {response.Status}");
}
```

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33require "json"
require "openai"

client = OpenAI::Client.new
response = client.responses.create(
  model: "gpt-6-astra",
  input: [
    {
      role: :system,
      content: "You are a helpful assistant designed to output JSON."
    },
    {
      role: :user,
      content: "Who won the World Series in 2020? Respond in the format {winner: ...}."
    }
  ],
  text: { format: { type: :json_object } }
)

if response.status == OpenAI::Responses::ResponseStatus::INCOMPLETE
  warn("The JSON response is incomplete.")
else
  refusal = response.output
                    .grep(OpenAI::Models::Responses::ResponseOutputMessage)
                    .flat_map(&:content)
                    .find { |content| content.is_a?(OpenAI::Models::Responses::ResponseOutputRefusal) }

  if refusal.is_a?(OpenAI::Models::Responses::ResponseOutputRefusal)
    puts(refusal.refusal)
  elsif response.status == OpenAI::Responses::ResponseStatus::COMPLETED
    puts(JSON.pretty_generate(JSON.parse(response.output_text)))
  end
end
```

## Resources

To learn more about Structured Outputs, we recommend browsing the following resources:

*   Check out our [introductory cookbook](https://developers.openai.com/cookbook/examples/structured_outputs_intro) on Structured Outputs
*   Learn [how to build multi-agent systems](https://developers.openai.com/cookbook/examples/structured_outputs_multi_agent) with Structured Outputs

[Previous Code generation](https://developers.openai.com/api/docs/guides/code-generation)

Ask AI

## Docs agent

Loading docs agent...