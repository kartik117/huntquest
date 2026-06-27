export interface Checkpoint {
  id: string;
  name: string;
  clue: string;
  lat: number;
  lng: number;
  radius_m: number;
}

export interface Hunt {
  id: string;
  name: string;
  city: string;
  join_code: string;
  checkpoints: Checkpoint[];
}

export interface TeamScore {
  team_id: string;
  name: string;
  checkpoints_found: number;
  player_count: number;
}

export interface Session {
  playerId: string;
  teamId: string;
  sessionToken: string;
  displayName: string;
}

export interface PlayerPosition {
  playerId: string;
  teamId: string;
  displayName: string;
  lat: number;
  lng: number;
}

export type HuntEvent =
  | {
      type: 'location';
      player_id: string;
      team_id: string;
      display_name: string;
      lat: number;
      lng: number;
    }
  | {
      type: 'checkpoint_found';
      team_id: string;
      checkpoint_id: string;
      checkpoint_name: string;
      found_by: string;
    };
