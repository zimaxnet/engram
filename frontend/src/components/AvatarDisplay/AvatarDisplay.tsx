/**
 * AvatarDisplay Component
 * 
 * Renders the agent avatar with:
 * - Static portrait display
 * - Speaking animation
 * - Expression changes
 * - Viseme-based lip-sync (when available)
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import './AvatarDisplay.css';

// Viseme to mouth shape mapping
const VISEME_MOUTH_SHAPES: Record<number, {
  jawOpen: number;
  mouthWidth: number;
}> = {
  0: { jawOpen: 0, mouthWidth: 0.5 },      // silence
  1: { jawOpen: 0.6, mouthWidth: 0.6 },    // aa
  2: { jawOpen: 0.5, mouthWidth: 0.5 },    // aa
  3: { jawOpen: 0.4, mouthWidth: 0.4 },    // ao
  4: { jawOpen: 0.3, mouthWidth: 0.7 },    // ey
  5: { jawOpen: 0.3, mouthWidth: 0.5 },    // er
  6: { jawOpen: 0.2, mouthWidth: 0.6 },    // ih
  7: { jawOpen: 0.2, mouthWidth: 0.3 },    // uw
  8: { jawOpen: 0.4, mouthWidth: 0.3 },    // ow
  9: { jawOpen: 0.5, mouthWidth: 0.5 },    // aw
  10: { jawOpen: 0.3, mouthWidth: 0.4 },   // oy
  11: { jawOpen: 0.4, mouthWidth: 0.6 },   // ay
  12: { jawOpen: 0.3, mouthWidth: 0.5 },   // h
  13: { jawOpen: 0.2, mouthWidth: 0.4 },   // r
  14: { jawOpen: 0.2, mouthWidth: 0.5 },   // l
  15: { jawOpen: 0.1, mouthWidth: 0.6 },   // s
  16: { jawOpen: 0.1, mouthWidth: 0.4 },   // sh
  17: { jawOpen: 0.1, mouthWidth: 0.5 },   // th
  18: { jawOpen: 0.1, mouthWidth: 0.4 },   // f
  19: { jawOpen: 0.2, mouthWidth: 0.5 },   // d
  20: { jawOpen: 0.15, mouthWidth: 0.5 },  // k
  21: { jawOpen: 0, mouthWidth: 0.5 },     // p (closed)
};

interface Viseme {
  time_ms: number;
  viseme_id: number;
}

interface AvatarDisplayProps {
  agentId: 'elena' | 'marcus';
  isSpeaking?: boolean;
  expression?: 'neutral' | 'smile' | 'thinking' | 'listening';
  visemes?: Viseme[];
  showName?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const AGENT_INFO = {
  elena: {
    name: 'Dr. Elena Vasquez',
    role: 'Business Analyst',
    accentColor: '#00d4ff',
    imagePlaceholder: 'E',
  },
  marcus: {
    name: 'Marcus Chen',
    role: 'Project Manager',
    accentColor: '#a855f7',
    imagePlaceholder: 'M',
  },
};

export default function AvatarDisplay({
  agentId,
  isSpeaking = false,
  expression = 'neutral',
  visemes = [],
  showName = true,
  size = 'md',
}: AvatarDisplayProps) {
  const [currentVisemeId, setCurrentVisemeId] = useState(0);
  const [mouthShape, setMouthShape] = useState(VISEME_MOUTH_SHAPES[0]);
  const animationStartTime = useRef<number>(0);
  const animationFrameRef = useRef<number>(0);

  const agent = AGENT_INFO[agentId];

  // Animate visemes when speaking
  useEffect(() => {
    if (isSpeaking && visemes.length > 0) {
      animationStartTime.current = performance.now();
      
      const animate = () => {
        const elapsed = performance.now() - animationStartTime.current;
        
        // Find current viseme based on elapsed time
        let currentViseme = visemes[0];
        for (const v of visemes) {
          if (v.time_ms <= elapsed) {
            currentViseme = v;
          } else {
            break;
          }
        }
        
        setCurrentVisemeId(currentViseme.viseme_id);
        setMouthShape(VISEME_MOUTH_SHAPES[currentViseme.viseme_id] || VISEME_MOUTH_SHAPES[0]);
        
        // Continue animation if still speaking and not past last viseme
        const lastViseme = visemes[visemes.length - 1];
        if (elapsed < lastViseme.time_ms + 200) {
          animationFrameRef.current = requestAnimationFrame(animate);
        }
      };
      
      animationFrameRef.current = requestAnimationFrame(animate);
      
      return () => {
        cancelAnimationFrame(animationFrameRef.current);
      };
    } else {
      // Reset to neutral
      setCurrentVisemeId(0);
      setMouthShape(VISEME_MOUTH_SHAPES[0]);
    }
  }, [isSpeaking, visemes]);

  // Generate random speaking animation if no visemes
  useEffect(() => {
    if (isSpeaking && visemes.length === 0) {
      const interval = setInterval(() => {
        const randomViseme = Math.floor(Math.random() * 12) + 1; // Random mouth shape
        setMouthShape(VISEME_MOUTH_SHAPES[randomViseme] || VISEME_MOUTH_SHAPES[0]);
      }, 100);
      
      return () => clearInterval(interval);
    }
  }, [isSpeaking, visemes]);

  const getExpressionStyle = useCallback(() => {
    switch (expression) {
      case 'smile':
        return { filter: 'brightness(1.1)' };
      case 'thinking':
        return { filter: 'brightness(0.95)' };
      case 'listening':
        return { filter: 'brightness(1.05)' };
      default:
        return {};
    }
  }, [expression]);

  return (
    <div className={`avatar-display avatar-${size}`}>
      {/* Avatar Circle */}
      <div 
        className={`avatar-circle ${isSpeaking ? 'speaking' : ''}`}
        style={{
          '--accent-color': agent.accentColor,
          ...getExpressionStyle(),
        } as React.CSSProperties}
      >
        {/* Glow rings when speaking */}
        {isSpeaking && (
          <>
            <div className="avatar-glow-ring ring-1" />
            <div className="avatar-glow-ring ring-2" />
            <div className="avatar-glow-ring ring-3" />
          </>
        )}
        
        {/* Avatar Image/Placeholder */}
        <div className="avatar-image">
          <span className="avatar-placeholder">
            {agent.imagePlaceholder}
          </span>
        </div>
        
        {/* Animated Mouth Overlay (CSS-based) */}
        {isSpeaking && (
          <div 
            className="avatar-mouth"
            style={{
              '--jaw-open': mouthShape.jawOpen,
              '--mouth-width': mouthShape.mouthWidth,
            } as React.CSSProperties}
          />
        )}
        
        {/* Expression Indicator */}
        <div className={`avatar-expression ${expression}`} />
      </div>
      
      {/* Agent Info */}
      {showName && (
        <div className="avatar-info">
          <span className="avatar-name">{agent.name}</span>
          <span className="avatar-role">{agent.role}</span>
          {isSpeaking && (
            <span className="avatar-status speaking">
              <span className="status-dot" />
              Speaking
            </span>
          )}
        </div>
      )}
    </div>
  );
}

