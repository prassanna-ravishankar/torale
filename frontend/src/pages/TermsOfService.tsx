import { useNavigate } from "react-router-dom"
import { Logo } from "@/components/Logo"
import { ArrowLeft } from "lucide-react"

export function TermsOfService() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#fafafa]">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full bg-[#fafafa]/90 backdrop-blur-md border-b border-zinc-200">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="cursor-pointer">
            <Logo />
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-sm font-bold text-zinc-900 hover:text-[hsl(10,90%,55%)] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto max-w-4xl px-6 py-16">
        <div className="bg-white border-2 border-zinc-200 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.1)] p-12">
          <h1 className="text-4xl font-bold font-grotesk text-zinc-900 mb-2">Terms of Service</h1>
          <p className="text-sm text-zinc-500 font-mono mb-12">Effective Date: December 2, 2025</p>

          <div className="prose prose-zinc max-w-none space-y-8">
            {/* Acceptance */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">1. Acceptance of Terms</h2>
              <p className="text-zinc-600 leading-relaxed">
                By accessing or using Torale ("Service"), you agree to be bound by these Terms of Service ("Terms").
                If you disagree with any part of the Terms, you may not access the Service.
              </p>
            </section>

            {/* Service Description */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">2. Service Description</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                Torale is a web monitoring platform that performs automated search queries, evaluates conditions using
                large language models (LLMs), and sends notifications when specified criteria are met.
              </p>
              <p className="text-zinc-600 leading-relaxed">
                The Service uses third-party AI providers (Google Gemini, OpenAI, Anthropic) to analyze web content
                and determine whether monitoring conditions have been satisfied.
              </p>
            </section>

            {/* User Accounts */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">3. User Accounts and Authentication</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                You may create an account using email/password authentication or OAuth providers (Google, GitHub) via
                our authentication service provider, Clerk.
              </p>
              <p className="text-zinc-600 leading-relaxed mb-4">
                You are responsible for:
              </p>
              <ul className="list-disc pl-6 text-zinc-600 space-y-2">
                <li>Maintaining the confidentiality of your account credentials and API keys</li>
                <li>All activities that occur under your account</li>
                <li>Notifying us immediately of any unauthorized access or security breach</li>
              </ul>
              <p className="text-zinc-600 leading-relaxed mt-4">
                We reserve the right to suspend or terminate accounts that violate these Terms or engage in abusive behavior.
              </p>
            </section>

            {/* Acceptable Use */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">4. Acceptable Use</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">You agree NOT to use the Service to:</p>
              <ul className="list-disc pl-6 text-zinc-600 space-y-2">
                <li>Monitor websites in violation of their Terms of Service or robots.txt directives</li>
                <li>Scrape, crawl, or harvest data at rates that could be considered abusive or cause service degradation</li>
                <li>Monitor content for illegal purposes, including stalking, harassment, or unauthorized surveillance</li>
                <li>Attempt to reverse engineer, decompile, or extract source code from the Service</li>
                <li>Interfere with or disrupt the Service or servers/networks connected to the Service</li>
                <li>Bypass rate limits, usage quotas, or authentication mechanisms</li>
                <li>Use the Service to distribute malware, phishing attempts, or other malicious content</li>
              </ul>
            </section>

            {/* Data Collection & Admin Access */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">5. Data Collection and Administrative Access</h2>

              <div className="bg-amber-50 border-l-4 border-amber-500 p-6 mb-6">
                <h3 className="text-lg font-bold font-grotesk text-amber-900 mb-2">⚠️ Important Disclosure</h3>
                <p className="text-amber-800 text-sm leading-relaxed">
                  Torale operators have administrative access to platform data for operational, support, and analytical purposes.
                </p>
              </div>

              <p className="text-zinc-600 leading-relaxed mb-4">
                <strong className="text-zinc-900">Administrative Console Access:</strong> Authorized Torale administrators
                may access an administrative console ("Admin Console") that provides visibility into:
              </p>
              <ul className="list-disc pl-6 text-zinc-600 space-y-2 mb-4">
                <li><strong>User Data:</strong> Email addresses, account creation dates, activity statistics, and account status</li>
                <li><strong>Task Configurations:</strong> Search queries, condition descriptions, schedules, and notification preferences you have configured</li>
                <li><strong>Execution History:</strong> Results from automated task executions, including LLM-generated answers, grounding sources, and condition evaluation outcomes</li>
                <li><strong>System Metrics:</strong> Platform-wide statistics including popular search queries, execution success rates, and error logs</li>
                <li><strong>Scheduling Data:</strong> Job execution status, schedules, and debugging information for task orchestration</li>
              </ul>

              <p className="text-zinc-600 leading-relaxed mb-4">
                <strong className="text-zinc-900">Purpose of Access:</strong> Administrative access is used exclusively for:
              </p>
              <ul className="list-disc pl-6 text-zinc-600 space-y-2 mb-4">
                <li>Providing customer support and troubleshooting technical issues</li>
                <li>Monitoring system health, performance, and security</li>
                <li>Detecting and preventing abusive behavior or Terms violations</li>
                <li>Improving Service quality through aggregate analytics</li>
                <li>Ensuring compliance with legal obligations</li>
              </ul>

              <p className="text-zinc-600 leading-relaxed mb-4">
                <strong className="text-zinc-900">Data Retention:</strong> We retain execution history, task configurations,
                and user data for the duration of your account plus 90 days after account deletion for legal and operational purposes.
              </p>

              <p className="text-zinc-600 leading-relaxed">
                <strong className="text-zinc-900">Your Rights:</strong> You may request data deletion, export your data,
                or deactivate your account at any time by contacting <a href="mailto:support@torale.ai" className="text-[hsl(10,90%,55%)] hover:underline">support@torale.ai</a>.
              </p>
            </section>

            {/* Third-Party Services */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">6. Third-Party Services and AI Providers</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                The Service integrates with third-party providers:
              </p>
              <ul className="list-disc pl-6 text-zinc-600 space-y-2">
                <li><strong>AI/LLM Providers:</strong> Google Gemini (primary), OpenAI, Anthropic Claude</li>
                <li><strong>Authentication:</strong> Clerk (user authentication and session management)</li>
                <li><strong>Infrastructure:</strong> Google Cloud Platform (compute, database, orchestration)</li>
                <li><strong>Task Scheduling:</strong> APScheduler (cron-based task scheduling and execution)</li>
              </ul>
              <p className="text-zinc-600 leading-relaxed mt-4">
                Your search queries and monitored content may be transmitted to these providers for processing.
                We recommend reviewing their respective privacy policies and terms of service.
              </p>
            </section>

            {/* Intellectual Property */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">7. Intellectual Property</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                <strong className="text-zinc-900">Service Ownership:</strong> The Service, including its source code,
                design, functionality, and documentation, is owned by Torale Labs Inc. and protected by copyright and
                other intellectual property laws.
              </p>
              <p className="text-zinc-600 leading-relaxed mb-4">
                <strong className="text-zinc-900">User Content:</strong> You retain ownership of your search queries,
                condition descriptions, and monitoring configurations ("User Content"). By using the Service, you grant
                us a worldwide, non-exclusive license to process, store, and transmit User Content as necessary to
                provide the Service.
              </p>
              <p className="text-zinc-600 leading-relaxed">
                <strong className="text-zinc-900">Open Source:</strong> Portions of the Service are released under the
                MIT License. See our <a href="https://github.com/prassanna-ravishankar/torale" target="_blank" rel="noopener noreferrer" className="text-[hsl(10,90%,55%)] hover:underline">GitHub repository</a> for details.
              </p>
            </section>

            {/* Beta Access & Pricing */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">8. Beta Access and Pricing</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                <strong className="text-zinc-900">Beta Status:</strong> The Service is currently in beta. Features may
                change, and availability is not guaranteed. We may introduce usage limits, feature restrictions, or
                paid plans in the future with reasonable notice.
              </p>
              <p className="text-zinc-600 leading-relaxed">
                <strong className="text-zinc-900">User Capacity Limits:</strong> Access may be restricted during beta
                to manage system load. Waitlisted users will be admitted based on available capacity.
              </p>
            </section>

            {/* Disclaimers */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">9. Disclaimers and Limitations of Liability</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
                BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
              </p>
              <p className="text-zinc-600 leading-relaxed mb-4">
                WE DO NOT GUARANTEE:
              </p>
              <ul className="list-disc pl-6 text-zinc-600 space-y-2 mb-4">
                <li>Accuracy, completeness, or timeliness of search results or LLM-generated responses</li>
                <li>Uninterrupted or error-free operation of the Service</li>
                <li>That monitoring conditions will be correctly evaluated in all cases</li>
                <li>That notifications will be delivered within any specific timeframe</li>
              </ul>
              <p className="text-zinc-600 leading-relaxed">
                IN NO EVENT SHALL TORALE LABS INC. BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR
                PUNITIVE DAMAGES ARISING OUT OF OR RELATED TO YOUR USE OF THE SERVICE.
              </p>
            </section>

            {/* Termination */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">10. Termination</h2>
              <p className="text-zinc-600 leading-relaxed mb-4">
                We may suspend or terminate your access to the Service at any time, with or without cause or notice,
                including for violations of these Terms.
              </p>
              <p className="text-zinc-600 leading-relaxed">
                You may terminate your account at any time by contacting <a href="mailto:support@torale.ai" className="text-[hsl(10,90%,55%)] hover:underline">support@torale.ai</a>.
                Upon termination, your data will be retained for 90 days before permanent deletion.
              </p>
            </section>

            {/* Changes to Terms */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">11. Changes to Terms</h2>
              <p className="text-zinc-600 leading-relaxed">
                We reserve the right to modify these Terms at any time. Material changes will be communicated via email
                or in-app notification. Continued use of the Service after changes constitutes acceptance of the revised Terms.
              </p>
            </section>

            {/* Governing Law */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">12. Governing Law and Dispute Resolution</h2>
              <p className="text-zinc-600 leading-relaxed">
                These Terms are governed by the laws of the State of Delaware, United States, without regard to conflict
                of law principles. Any disputes shall be resolved through binding arbitration in accordance with the
                American Arbitration Association's rules.
              </p>
            </section>

            {/* Contact */}
            <section>
              <h2 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">13. Contact Information</h2>
              <p className="text-zinc-600 leading-relaxed">
                For questions about these Terms, contact us at:
              </p>
              <div className="mt-4 p-4 bg-zinc-50 border border-zinc-200 rounded font-mono text-sm">
                <p className="text-zinc-900">Torale Labs Inc.</p>
                <p className="text-zinc-600">Email: <a href="mailto:legal@torale.ai" className="text-[hsl(10,90%,55%)] hover:underline">legal@torale.ai</a></p>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}
