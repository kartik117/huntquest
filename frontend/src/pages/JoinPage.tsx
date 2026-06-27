import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DEMO_HUNT_ID, joinHunt } from '../api';
import { Session } from '../types';

const STORAGE_KEY = 'huntquest.session';

export function JoinPage() {
  const [displayName, setDisplayName] = useState('');
  const [teamName, setTeamName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await joinHunt(DEMO_HUNT_ID, displayName.trim(), teamName.trim());
      const session: Session = {
        playerId: res.player_id,
        teamId: res.team_id,
        sessionToken: res.session_token,
        displayName: displayName.trim(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
      navigate('/map');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="join-card">
      <h1>🧭 HuntQuest</h1>
      <p className="muted">Seattle Landmarks Hunt -- find real landmarks with your team, live on the map.</p>
      <form onSubmit={handleSubmit}>
        <label>
          Your name
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required maxLength={80} />
        </label>
        <label>
          Team name
          <input value={teamName} onChange={(e) => setTeamName(e.target.value)} required maxLength={80} />
          <span className="hint">Use the same team name as your teammates to join them.</span>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Joining...' : 'Start hunting'}
        </button>
      </form>
    </div>
  );
}

export function loadSession(): Session | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
