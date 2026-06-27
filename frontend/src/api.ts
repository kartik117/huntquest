import { Hunt, TeamScore } from './types';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000';
export const DEMO_HUNT_ID = import.meta.env.VITE_DEMO_HUNT_ID ?? '11111111-1111-1111-1111-111111111111';

export async function getHunt(huntId: string): Promise<Hunt> {
  const res = await fetch(`${API_URL}/hunts/${huntId}`);
  if (!res.ok) throw new Error(`Hunt not found (${res.status})`);
  return res.json();
}

export async function joinHunt(
  huntId: string,
  displayName: string,
  teamName: string
): Promise<{ player_id: string; team_id: string; session_token: string }> {
  const res = await fetch(`${API_URL}/hunts/${huntId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: displayName, team_name: teamName }),
  });
  if (!res.ok) throw new Error(`Could not join hunt (${res.status})`);
  return res.json();
}

export async function getLeaderboard(huntId: string): Promise<TeamScore[]> {
  const res = await fetch(`${API_URL}/hunts/${huntId}/teams`);
  if (!res.ok) throw new Error(`Could not load leaderboard (${res.status})`);
  return res.json();
}
