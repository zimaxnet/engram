import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './App.css';
import { MainLayout } from './components/MainLayout';
import { ChatView } from './pages/Chat/ChatView';
import { AgentsPage } from './pages/Agents/AgentsPage';
import { useKeepAlive } from './hooks/useKeepAlive';
import { type AgentId } from './types';
import { SourcesPage } from './pages/Sources/SourcesPage';
import { KnowledgeGraph } from './pages/Memory/KnowledgeGraph';
import { Episodes } from './pages/Memory/Episodes';
import { Search } from './pages/Memory/Search';
import { ActiveWorkflows } from './pages/Workflows/ActiveWorkflows';
import { WorkflowHistory } from './pages/Workflows/WorkflowHistory';
import { SignalsDelegate } from './pages/Workflows/SignalsDelegate';
import { WorkflowDetail } from './pages/Workflows/WorkflowDetail';
import { GeneralSettings } from './pages/Settings/GeneralSettings';
import { UserManagement } from './pages/Admin/UserManagement';
import { SystemHealth } from './pages/Admin/SystemHealth';
import { GoldenThreadRunner } from './pages/Validation/GoldenThreadRunner';
import { EvidenceTelemetry } from './pages/Evidence/EvidenceTelemetry';
import { BAUHub } from './pages/BAU/BAUHub';
import { VoiceInteractionPage } from './pages/Voice/VoiceInteractionPage';
import { StoriesPage } from './pages/Stories/StoriesPage';
import { StoryDetail } from './pages/Stories/StoryDetail';

function AppContent() {
  const location = useLocation();
  const [activeAgent, setActiveAgent] = useState<AgentId>('elena');
  const [selectedModel, setSelectedModel] = useState('gpt-5-chat');
  
  // Single conversation/session ID shared across Chat + Voice so both persist into the same Zep session.
  // Can be overridden via navigation state (e.g., from Episodes page)
  const [sessionId, setSessionId] = useState<string>(() => {
    const key = 'engram_session_id'
    const fallback = `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    try {
      const existing = sessionStorage.getItem(key)
      if (existing) return existing
      sessionStorage.setItem(key, fallback)
      return fallback
    } catch {
      return fallback
    }
  });

  // Update session ID and agent when navigating from Episodes
  useEffect(() => {
    const state = location.state as { sessionId?: string; agentId?: string } | null;
    if (state?.sessionId) {
      try {
        sessionStorage.setItem('engram_session_id', state.sessionId);
        setSessionId(state.sessionId);
      } catch (err) {
        console.error('Failed to update session ID:', err);
      }
    }
    if (state?.agentId && ['elena', 'marcus', 'sage'].includes(state.agentId)) {
      setActiveAgent(state.agentId as AgentId);
    }
  }, [location.state]);

  return (
    <Routes>
      <Route
        path="/"
        element={
          <MainLayout
            activeAgent={activeAgent}
            onAgentChange={setActiveAgent}
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
            sessionId={sessionId}
          />
        }
      >
          {/* Main Chat Interface */}
          <Route index element={<ChatView />} />

          {/* Voice Interaction */}
          <Route path="voice" element={<VoiceInteractionPage activeAgent={activeAgent} sessionId={sessionId} />} />

          {/* Agents Information */}
          <Route path="agents" element={<AgentsPage />} />

          {/* Sources / Unstructured intake */}
          <Route path="sources" element={<SourcesPage />} />

          {/* Validation & Evidence */}
          <Route path="validation">
            <Route path="golden-thread" element={<GoldenThreadRunner />} />
            <Route index element={<Navigate to="golden-thread" replace />} />
          </Route>
          <Route path="evidence" element={<EvidenceTelemetry />} />

          {/* Stories Artifacts */}
          <Route path="stories">
            <Route index element={<StoriesPage />} />
            <Route path=":storyId" element={<StoryDetail />} />
          </Route>

          {/* BAU Adoption */}
          <Route path="bau" element={<BAUHub />} />

          {/* Memory Section */}
          <Route path="memory">
            <Route path="graph" element={<KnowledgeGraph />} />
            <Route path="episodes" element={<Episodes />} />
            <Route path="search" element={<Search />} />
          </Route>

          {/* Workflows Section */}
          <Route path="workflows">
            <Route path="active" element={<ActiveWorkflows />} />
            <Route path="history" element={<WorkflowHistory />} />
            <Route path="signals" element={<SignalsDelegate />} />
            <Route path=":workflowId" element={<WorkflowDetail />} />
            {/* Default for /workflows if no sub-path matches */}
            <Route index element={<Navigate to="active" replace />} />
          </Route>

          {/* Settings Section */}
          <Route path="settings">
            <Route path="general" element={<GeneralSettings />} />
            <Route index element={<Navigate to="general" replace />} />
          </Route>

          {/* Admin Section */}
          <Route path="admin">
            <Route path="users" element={<UserManagement />} />
            <Route path="health" element={<SystemHealth />} />
            <Route index element={<Navigate to="health" replace />} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
  );
}

function App() {
  // Keep backend containers warm while user is active
  useKeepAlive();

  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
