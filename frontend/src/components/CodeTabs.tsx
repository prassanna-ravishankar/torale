import { useState } from 'react';

type CodeTab = 'cli' | 'api' | 'python' | 'self-hosted';

export function CodeTabs() {
  const [activeTab, setActiveTab] = useState<CodeTab>('cli');

  const tabs: { id: CodeTab; label: string }[] = [
    { id: 'cli', label: '[ CLI ]' },
    { id: 'api', label: '[ API (curl) ]' },
    { id: 'python', label: '[ Python SDK ]' },
    { id: 'self-hosted', label: '[ Self-Hosted ]' },
  ];

  const codeExamples: Record<CodeTab, string> = {
    cli: `<span class="text-brand-red">$</span> torale auth set-api-key

<span class="text-brand-red">$</span> torale task create \\
    --query "When is iPhone 16 being released?" \\
    --condition "A specific release date is announced" \\
    --schedule "0 9 * * *" \\
    --notify-behavior once

<span class="text-brand-red">$</span> torale task list`,

    api: `<span class="text-brand-red">$</span> curl -X POST https://api.torale.ai/api/v1/tasks \\
  -H "Authorization: Bearer sk_your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "iPhone Release Monitor",
    "schedule": "0 9 * * *",
    "search_query": "When is iPhone 16 being released?",
    "condition_description": "A specific release date is announced",
    "notify_behavior": "once"
  }'`,

    python: `<span class="text-brand-red">from</span> torale.sdk <span class="text-brand-red">import</span> ToraleClient

client = ToraleClient(
    api_key=<span class="text-green-400">"sk_your_api_key"</span>,
    base_url=<span class="text-green-400">"https://api.torale.ai"</span>
)

task = client.tasks.create(
    name=<span class="text-green-400">"iPhone Release Monitor"</span>,
    search_query=<span class="text-green-400">"When is iPhone 16 being released?"</span>,
    condition_description=<span class="text-green-400">"A specific release date is announced"</span>,
    schedule=<span class="text-green-400">"0 9 * * *"</span>,
    notify_behavior=<span class="text-green-400">"once"</span>
)`,

    'self-hosted': `<span class="text-brand-red"># 1. Clone the repository</span>
<span class="text-brand-red">$</span> git clone https://github.com/prassanna-ravishankar/torale
<span class="text-brand-red">$</span> cd torale

<span class="text-brand-red"># 2. Configure environment</span>
<span class="text-brand-red">$</span> cp .env.example .env
<span class="text-brand-red"># Add your API keys (GOOGLE_API_KEY, etc.)</span>

<span class="text-brand-red"># 3. Start all services</span>
<span class="text-brand-red">$</span> docker compose up -d

<span class="text-brand-red"># 4. Start frontend</span>
<span class="text-brand-red">$</span> cd frontend && npm run dev

<span class="text-brand-red"># 5. Open http://localhost:3000</span>`,
  };

  return (
    <div className="max-w-3xl mx-auto bg-black text-white p-6">
      {/* Code Tabs */}
      <div className="flex gap-x-6 mb-4 font-mono text-sm flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`code-tab-btn pb-2 transition-colors ${
              activeTab === tab.id
                ? 'code-active-tab text-brand-red'
                : 'text-brand-grey hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Code Content */}
      <pre className="font-mono text-sm overflow-x-auto">
        <code
          dangerouslySetInnerHTML={{ __html: codeExamples[activeTab] }}
        />
      </pre>
    </div>
  );
}
