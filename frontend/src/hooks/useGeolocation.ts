import { useRef, useState } from 'react';

interface UseGeolocationResult {
  sharing: boolean;
  error: string | null;
  startSharing: () => void;
  stopSharing: () => void;
}

/**
 * Wraps the real browser Geolocation API (navigator.geolocation.watchPosition) --
 * on a phone this is the device's actual GPS. Geolocation is only available on
 * https:// or http://localhost, which is fine for local dev/demo but worth
 * knowing if this is ever deployed somewhere without TLS.
 */
export function useGeolocation(onPosition: (lat: number, lng: number) => void): UseGeolocationResult {
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const watchIdRef = useRef<number | null>(null);

  function startSharing() {
    if (!navigator.geolocation) {
      setError('Geolocation is not available in this browser');
      return;
    }
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setError(null);
        onPosition(pos.coords.latitude, pos.coords.longitude);
      },
      (err) => setError(err.message),
      { enableHighAccuracy: true, maximumAge: 2000, timeout: 10000 }
    );
    setSharing(true);
  }

  function stopSharing() {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setSharing(false);
  }

  return { sharing, error, startSharing, stopSharing };
}
