import { CircleMarker, MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Checkpoint, PlayerPosition } from '../types';

// Default Leaflet marker icons reference image files via relative URLs that
// don't survive a Vite bundle -- rebuilding the icon from the CDN-hosted
// assets is the standard workaround rather than vendoring the PNGs.
const checkpointIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const TEAM_COLORS = ['#4f7cff', '#ff6b6b', '#4fd1a5', '#f5b942', '#a78bfa'];

function colorForTeam(teamId: string): string {
  let hash = 0;
  for (const ch of teamId) hash = (hash * 31 + ch.charCodeAt(0)) % TEAM_COLORS.length;
  return TEAM_COLORS[hash];
}

interface Props {
  center: [number, number];
  checkpoints: Checkpoint[];
  foundCheckpointIds: Set<string>;
  positions: PlayerPosition[];
}

export function HuntMap({ center, checkpoints, foundCheckpointIds, positions }: Props) {
  return (
    <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {checkpoints.map((cp) => (
        <Marker key={cp.id} position={[cp.lat, cp.lng]} icon={checkpointIcon}>
          <Popup>
            <strong>{cp.name}</strong>
            <br />
            {foundCheckpointIds.has(cp.id) ? '✅ Found by your team' : cp.clue}
          </Popup>
        </Marker>
      ))}
      {positions.map((p) => (
        <CircleMarker
          key={p.playerId}
          center={[p.lat, p.lng]}
          radius={9}
          pathOptions={{ color: colorForTeam(p.teamId), fillOpacity: 0.85 }}
        >
          <Popup>{p.displayName}</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
