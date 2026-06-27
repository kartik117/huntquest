import { useEffect, useRef, useState } from 'react';
import { WS_URL } from '../api';
import { HuntEvent, PlayerPosition } from '../types';

export interface CheckpointFoundEvent {
  checkpointId: string;
  checkpointName: string;
  teamId: string;
  foundBy: string;
}

interface UseHuntSocketResult {
  positions: Map<string, PlayerPosition>;
  recentFinds: CheckpointFoundEvent[];
  sendLocation: (lat: number, lng: number) => void;
  connected: boolean;
}

export function useHuntSocket(huntId: string, sessionToken: string | null): UseHuntSocketResult {
  const [positions, setPositions] = useState<Map<string, PlayerPosition>>(new Map());
  const [recentFinds, setRecentFinds] = useState<CheckpointFoundEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionToken) return;

    const ws = new WebSocket(`${WS_URL}/ws/hunts/${huntId}?token=${sessionToken}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const data: HuntEvent = JSON.parse(event.data);
      if (data.type === 'location') {
        setPositions((prev) => {
          const next = new Map(prev);
          next.set(data.player_id, {
            playerId: data.player_id,
            teamId: data.team_id,
            displayName: data.display_name,
            lat: data.lat,
            lng: data.lng,
          });
          return next;
        });
      } else if (data.type === 'checkpoint_found') {
        const find: CheckpointFoundEvent = {
          checkpointId: data.checkpoint_id,
          checkpointName: data.checkpoint_name,
          teamId: data.team_id,
          foundBy: data.found_by,
        };
        setRecentFinds((prev) => [find, ...prev].slice(0, 5));
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [huntId, sessionToken]);

  function sendLocation(lat: number, lng: number) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'location', lat, lng }));
    }
  }

  return { positions, recentFinds, sendLocation, connected };
}
