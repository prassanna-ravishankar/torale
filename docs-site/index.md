---
layout: home

hero:
  name: Torale
  text: Grounded Search Monitoring
  tagline: Automate web monitoring with AI-powered conditional automation
  image:
    src: /logo.svg
    alt: Torale
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/torale-ai/torale
    - theme: alt
      text: Try Live App
      link: https://torale.ai

features:
  - icon: 🔍
    title: Grounded Search
    details: Monitor the web using Google Search combined with Gemini AI for intelligent condition evaluation

  - icon: ⏰
    title: Automated Scheduling
    details: Set custom cron schedules to automatically check conditions and notify you when they're met

  - icon: 📊
    title: State Tracking
    details: Track changes over time and get notified only when meaningful changes occur

  - icon: 🔔
    title: Smart Notifications
    details: Configure notification behavior - notify once, always, or track state changes

  - icon: 🎯
    title: Task Templates
    details: Pre-built templates for common monitoring scenarios like product releases and price tracking

  - icon: 🚀
    title: Easy Integration
    details: Use via web dashboard, CLI, or Python SDK for seamless workflow integration

  - icon: 🔐
    title: Secure Authentication
    details: OAuth via Clerk with Google and GitHub, plus API key support for CLI access

  - icon: ☁️
    title: Production-Ready
    details: Deployed on GKE with Temporal Cloud orchestration, auto-scaling, and cost optimization
---

## Quick Examples

**Monitor Product Releases**
```bash
torale task create \
  --query "When is the next iPhone being released?" \
  --condition "A specific release date has been officially announced" \
  --schedule "0 9 * * *"
```

**Track Price Changes**
```bash
torale task create \
  --query "What is the current price of PS5 at Best Buy?" \
  --condition "Price has dropped below $450" \
  --schedule "0 */4 * * *"
```

**Check Availability**
```bash
torale task create \
  --query "Are swimming pool memberships open for summer at SF Rec Center?" \
  --condition "Memberships are now available" \
  --schedule "0 8 * * *"
```

## Why Torale?

Traditional web monitoring requires:
- Manual checking of websites daily
- Setting up complex scrapers for dynamic content
- Missing important updates due to inconsistent checking

**Torale solves this by:**
1. **Grounded Search** - Uses Google Search via Gemini AI to find current information
2. **Intelligent Evaluation** - LLM understands context and evaluates if your condition is met
3. **Automated Execution** - Temporal workflows handle scheduling and retries
4. **Change Detection** - Compares results over time to avoid duplicate notifications

## Use Cases

- 📱 **Product Releases** - Get notified when release dates are announced
- 💰 **Price Tracking** - Monitor price changes for products you want to buy
- 🎫 **Availability Monitoring** - Track when items come back in stock
- 📰 **News Alerts** - Stay updated on specific topics or developments
- 🎉 **Event Announcements** - Know when tickets go on sale
- 🏊 **Service Availability** - Track when registrations open

## Get Started

<div style="display: flex; gap: 1rem; margin-top: 1rem;">
  <a href="/guide/getting-started" style="padding: 0.5rem 1rem; background: #3b82f6; color: white; text-decoration: none; border-radius: 0.5rem; font-weight: 500;">
    Read the Guide
  </a>
  <a href="https://torale.ai" style="padding: 0.5rem 1rem; border: 1px solid #3b82f6; color: #3b82f6; text-decoration: none; border-radius: 0.5rem; font-weight: 500;">
    Try Torale
  </a>
</div>
