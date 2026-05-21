import { MarketingLayout } from '@/components/marketing/MarketingLayout'
import { DynamicMeta } from '@/components/DynamicMeta'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'
import marketingStyles from '@/components/marketing/marketing.module.css'

export function TermsOfService() {
  return (
    <>
      <DynamicMeta
        path="/terms"
        title="Terms — webwhen"
        description="Terms of service for webwhen, the agent that waits for the web."
      />
      <MarketingLayout>
        <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
          <div className={landingStyles.container}>
            <div className={marketingStyles.reading}>
              <div className={marketingStyles.articleHeroEyebrow}>Terms</div>
              <h1 className={marketingStyles.articleHeading}>
                The terms for using <span className={marketingStyles.articleHeroEmber}>webwhen</span>.
              </h1>
              <p className={marketingStyles.articleLede}>
                Plain-English summary of what we agree to, both ways.
              </p>
              <p className={marketingStyles.stamp}>Last updated: December 2, 2025</p>
            </div>
          </div>
        </section>

        <section className={landingStyles.section}>
          <div className={landingStyles.container}>
            <div className={marketingStyles.reading}>
              <h2>1. Acceptance of Terms</h2>
              <p>
                By accessing or using webwhen ("Service"), you agree to be bound by these Terms of Service ("Terms").
                If you disagree with any part of the Terms, you may not access the Service.
              </p>

              <h2>2. Service Description</h2>
              <p>
                webwhen is a web monitoring platform that performs automated search queries, evaluates conditions using
                large language models (LLMs), and sends notifications when specified criteria are met.
              </p>
              <p>
                The Service uses third-party AI providers (Anthropic Claude, Perplexity) to analyze web content
                and determine whether monitoring conditions have been satisfied.
              </p>

              <h2>3. User Accounts and Authentication</h2>
              <p>
                You may create an account using email/password authentication or OAuth providers (Google, GitHub) via
                our authentication service provider, Clerk.
              </p>
              <p>You are responsible for:</p>
              <ul>
                <li>Maintaining the confidentiality of your account credentials and API keys</li>
                <li>All activities that occur under your account</li>
                <li>Notifying us immediately of any unauthorized access or security breach</li>
              </ul>
              <p>
                We reserve the right to suspend or terminate accounts that violate these Terms or engage in abusive behavior.
              </p>

              <h2>4. Acceptable Use</h2>
              <p>You agree NOT to use the Service to:</p>
              <ul>
                <li>Monitor websites in violation of their Terms of Service or robots.txt directives</li>
                <li>Scrape, crawl, or harvest data at rates that could be considered abusive or cause service degradation</li>
                <li>Monitor content for illegal purposes, including stalking, harassment, or unauthorized surveillance</li>
                <li>Attempt to reverse engineer, decompile, or extract source code from the Service</li>
                <li>Interfere with or disrupt the Service or servers/networks connected to the Service</li>
                <li>Bypass rate limits, usage quotas, or authentication mechanisms</li>
                <li>Use the Service to distribute malware, phishing attempts, or other malicious content</li>
              </ul>

              <h2>5. Data Collection and Administrative Access</h2>
              <p>
                webwhen operators have administrative access to platform data for operational, support, and analytical purposes.
              </p>
              <p>
                <strong>Administrative Console Access:</strong> Authorized webwhen administrators may access an
                administrative console ("Admin Console") that provides visibility into:
              </p>
              <ul>
                <li><strong>User Data:</strong> Email addresses, account creation dates, activity statistics, and account status</li>
                <li><strong>Task Configurations:</strong> Search queries, condition descriptions, schedules, and notification preferences you have configured</li>
                <li><strong>Execution History:</strong> Results from automated task executions, including LLM-generated answers, grounding sources, and condition evaluation outcomes</li>
                <li><strong>System Metrics:</strong> Platform-wide statistics including popular search queries, execution success rates, and error logs</li>
                <li><strong>Scheduling Data:</strong> Job execution status, schedules, and debugging information for task orchestration</li>
              </ul>
              <p>
                <strong>Purpose of Access:</strong> Administrative access is used exclusively for:
              </p>
              <ul>
                <li>Providing customer support and troubleshooting technical issues</li>
                <li>Monitoring system health, performance, and security</li>
                <li>Detecting and preventing abusive behavior or Terms violations</li>
                <li>Improving Service quality through aggregate analytics</li>
                <li>Ensuring compliance with legal obligations</li>
              </ul>
              <p>
                <strong>Data Retention:</strong> We retain execution history, task configurations,
                and user data for the duration of your account plus 90 days after account deletion for legal and operational purposes.
              </p>
              <p>
                <strong>Your Rights:</strong> You may request data deletion, export your data,
                or deactivate your account at any time by contacting <a href="mailto:support@webwhen.ai">support@webwhen.ai</a>.
              </p>

              <h2>6. Third-Party Services and AI Providers</h2>
              <p>The Service integrates with third-party providers:</p>
              <ul>
                <li><strong>AI/LLM Providers:</strong> Anthropic Claude (monitoring agent), Perplexity (search)</li>
                <li><strong>Authentication:</strong> Clerk (user authentication and session management)</li>
                <li><strong>Infrastructure:</strong> Google Cloud Platform (compute, database, orchestration)</li>
                <li><strong>Task Scheduling:</strong> APScheduler (cron-based task scheduling and execution)</li>
              </ul>
              <p>
                Your search queries and monitored content may be transmitted to these providers for processing.
                We recommend reviewing their respective privacy policies and terms of service.
              </p>

              <h2>7. Intellectual Property</h2>
              <p>
                <strong>Service Ownership:</strong> The Service, including its source code,
                design, functionality, and documentation, is owned by webwhen and protected by copyright and
                other intellectual property laws.
              </p>
              <p>
                <strong>User Content:</strong> You retain ownership of your search queries,
                condition descriptions, and monitoring configurations ("User Content"). By using the Service, you grant
                us a worldwide, non-exclusive license to process, store, and transmit User Content as necessary to
                provide the Service.
              </p>
              <p>
                <strong>Open Source:</strong> Portions of the Service are released under the
                MIT License. See our <a href="https://github.com/prassanna-ravishankar/webwhen" target="_blank" rel="noopener noreferrer">GitHub repository</a> for details.
              </p>

              <h2>8. Beta Access and Pricing</h2>
              <p>
                <strong>Beta Status:</strong> The Service is currently in beta. Features may
                change, and availability is not guaranteed. We may introduce usage limits, feature restrictions, or
                paid plans in the future with reasonable notice.
              </p>
              <p>
                <strong>User Capacity Limits:</strong> Access may be restricted during beta
                to manage system load. Waitlisted users will be admitted based on available capacity.
              </p>

              <h2>9. Disclaimers and Limitations of Liability</h2>
              <p>
                THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
                BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
              </p>
              <p>WE DO NOT GUARANTEE:</p>
              <ul>
                <li>Accuracy, completeness, or timeliness of search results or LLM-generated responses</li>
                <li>Uninterrupted or error-free operation of the Service</li>
                <li>That monitoring conditions will be correctly evaluated in all cases</li>
                <li>That notifications will be delivered within any specific timeframe</li>
              </ul>
              <p>
                IN NO EVENT SHALL WEBWHEN BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR
                PUNITIVE DAMAGES ARISING OUT OF OR RELATED TO YOUR USE OF THE SERVICE.
              </p>

              <h2>10. Termination</h2>
              <p>
                We may suspend or terminate your access to the Service at any time, with or without cause or notice,
                including for violations of these Terms.
              </p>
              <p>
                You may terminate your account at any time by contacting <a href="mailto:support@webwhen.ai">support@webwhen.ai</a>.
                Upon termination, your data will be retained for 90 days before permanent deletion.
              </p>

              <h2>11. Changes to Terms</h2>
              <p>
                We reserve the right to modify these Terms at any time. Material changes will be communicated via email
                or in-app notification. Continued use of the Service after changes constitutes acceptance of the revised Terms.
              </p>

              <h2>12. Governing Law and Dispute Resolution</h2>
              <p>
                These Terms are governed by the laws of the State of Delaware, United States, without regard to conflict
                of law principles. Any disputes shall be resolved through binding arbitration in accordance with the
                American Arbitration Association's rules.
              </p>

              <h2>13. Contact Information</h2>
              <p>For questions about these Terms, contact us at:</p>
              <p>
                webwhen<br />
                Email: <a href="mailto:legal@webwhen.ai">legal@webwhen.ai</a>
              </p>
            </div>
          </div>
        </section>
      </MarketingLayout>
    </>
  )
}
