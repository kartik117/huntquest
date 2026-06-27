import { TeamScore } from '../types';

interface Props {
  scores: TeamScore[];
  myTeamId: string;
}

export function Leaderboard({ scores, myTeamId }: Props) {
  return (
    <div className="leaderboard">
      <h3>Leaderboard</h3>
      <ol>
        {scores.map((s) => (
          <li key={s.team_id} className={s.team_id === myTeamId ? 'my-team' : ''}>
            <span>{s.name}</span>
            <span className="muted">
              {s.checkpoints_found} found · {s.player_count} player{s.player_count === 1 ? '' : 's'}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
