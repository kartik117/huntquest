import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DEMO_HUNT_ID, getHunt, getLeaderboard } from '../api';
import { useHuntSocket } from '../hooks/useHuntSocket';
import { useGeolocation } from '../hooks/useGeolocation';
import { HuntMap } from '../components/HuntMap';
import { Leaderboard } from '../components/Leaderboard';
import { Hunt, TeamScore } from '../types';
import { loadSession } from './JoinPage';

export function MapPage() {
  const navigate = useNavigate();
  const session = loadSession();
  const [hunt, setHunt] = useState<Hunt | null>(null);
  const [scores, setScores] = useState<TeamScore[]>([]);
  const [foundIds, setFoundIds] = useState<Set<string>>(new Set());

  const { positions, recentFinds, sendLocation, connected } = useHuntSocket(
    DEMO_HUNT_ID,
    session?.sessionToken ?? null
  );
  const geo = useGeolocation(sendLocation);

  useEffect(() => {
    if (!session) {
      navigate('/join');
      return;
    }
    getHunt(DEMO_HUNT_ID).then(setHunt);
    getLeaderboard(DEMO_HUNT_ID).then(setScores);
  }, [session, navigate]);

  // Refresh the leaderboard whenever a checkpoint is found anywhere in the hunt,
  // and track which checkpoints this player's own team has found so the map
  // can show "found" instead of the clue for those markers.
  useEffect(() => {
    if (recentFinds.length === 0) return;
    getLeaderboard(DEMO_HUNT_ID).then(setScores);
    const myTeamFinds = recentFinds.filter((f) => f.teamId === session?.teamId).map((f) => f.checkpointId);
    if (myTeamFinds.length > 0) {
      setFoundIds((prev) => new Set([...prev, ...myTeamFinds]));
    }
  }, [recentFinds, session?.teamId]);

  if (!session || !hunt) return <p className="muted">Loading hunt...</p>;

  return (
    <div className="map-page">
      <div className="map-area">
        <HuntMap
          center={[hunt.checkpoints[0]?.lat ?? 47.6062, hunt.checkpoints[0]?.lng ?? -122.3321]}
          checkpoints={hunt.checkpoints}
          foundCheckpointIds={foundIds}
          positions={Array.from(positions.values())}
        />
      </div>
      <div className="sidebar">
        <h2>{hunt.name}</h2>
        <p className="muted">{connected ? '🟢 Connected' : '🔴 Reconnecting...'}</p>

        {!geo.sharing ? (
          <button onClick={geo.startSharing}>📍 Share my location</button>
        ) : (
          <button onClick={geo.stopSharing}>Stop sharing</button>
        )}
        {geo.error && <p className="error">{geo.error}</p>}

        <Leaderboard scores={scores} myTeamId={session.teamId} />

        {recentFinds.length > 0 && (
          <div className="recent-finds">
            <h3>Recent discoveries</h3>
            <ul>
              {recentFinds.map((f, i) => (
                <li key={i}>
                  🎉 {f.foundBy} found <strong>{f.checkpointName}</strong>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
