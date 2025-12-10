import { useState } from 'react';
import { ChatPanel } from '../../components/ChatPanel/ChatPanel';
import { VisualPanel } from '../../components/VisualPanel/VisualPanel';
import { useOutletContext } from 'react-router-dom';
import type { Agent } from '../../types';

interface ChatViewContext {
    agent: Agent;
    selectedModel: string;
    onModelChange: (model: string) => void;
}

export function ChatView() {
    const { agent, selectedModel, onModelChange } = useOutletContext<ChatViewContext>();

    const [sessionMetrics, setSessionMetrics] = useState({
        tokensUsed: 0,
        latency: 0,
        memoryNodes: 0,
        duration: 0,
        turns: 0,
        cost: 0
    });

    return (
        <>
            {/* Middle Column - Chat Interface */}
            <section className="column column-center">
                <ChatPanel
                    key={agent.id}
                    agent={agent}
                    onMetricsUpdate={setSessionMetrics}
                />
            </section>

            {/* Right Column - Visual Panel */}
            <aside className="column column-right">
                <VisualPanel
                    agent={agent}
                    metrics={sessionMetrics}
                    model={selectedModel}
                    onModelChange={onModelChange}
                />
            </aside>
        </>
    );
}
