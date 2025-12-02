import { CheckCircle2 } from 'lucide-react';

/**
 * TerminalSection - CLI demonstration terminal
 * From MockLandingPage.tsx lines 316-381
 */
export const TerminalSection = () => {
  return (
    <div className="w-full bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800 shadow-2xl font-mono text-sm">
      <div className="bg-zinc-900 px-4 py-2 flex items-center gap-2 border-b border-zinc-800">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
          <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
        </div>
        <div className="ml-auto text-zinc-600 text-xs">user@dev:~/monitors</div>
      </div>

      <div className="p-8 text-zinc-300 space-y-6">
        <div>
          <div className="flex gap-2 mb-2">
            <span className="text-[hsl(10,90%,55%)]">➜</span>
            <span className="text-zinc-500">~</span>
            <span>pip install torale</span>
          </div>
          <div className="text-zinc-500 pl-6 text-xs">
            Successfully installed torale-2.0.0
          </div>
        </div>

        <div>
          <div className="flex gap-2 mb-2">
            <span className="text-[hsl(10,90%,55%)]">➜</span>
            <span className="text-zinc-500">~/monitors</span>
            <span>torale create "Competitor Pricing" \</span>
          </div>
          <div className="pl-6 border-l-2 border-zinc-800 ml-1">
            <div className="flex gap-2">
              <span className="text-purple-400">--url</span>
              <span className="text-green-400">"https://competitor.com/pricing"</span>
              <span>\</span>
            </div>
            <div className="flex gap-2">
              <span className="text-purple-400">--extract</span>
              <span className="text-green-400">"enterprise_tier_cost"</span>
              <span>\</span>
            </div>
            <div className="flex gap-2">
              <span className="text-purple-400">--alert-on</span>
              <span className="text-green-400">"change"</span>
            </div>
          </div>
        </div>

        <div className="pl-6 pt-2">
          <div className="text-[hsl(10,90%,55%)] flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-4 h-4" />
            <span>Monitor deployed successfully</span>
          </div>
          <div className="text-zinc-600 text-xs">ID: mon_8e92f-22a1</div>
          <div className="text-zinc-600 text-xs">Status: Active (5min interval)</div>
        </div>

        <div className="flex gap-2">
          <span className="text-[hsl(10,90%,55%)]">➜</span>
          <span className="text-zinc-500">~/monitors</span>
          <span className="w-2 h-5 bg-zinc-500 animate-pulse block"></span>
        </div>
      </div>
    </div>
  );
};
