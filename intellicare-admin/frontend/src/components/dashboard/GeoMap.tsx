import { useEffect, useRef } from 'react';
import type { GeoRegion } from '@/types/index';
import { formatNumber, formatPercent } from '@utils/formatters';

interface GeoMapProps {
  data: GeoRegion[];
  title?: string;
  height?: number;
}

/**
 * Geographic map using Leaflet.
 * Shows patient distribution by region with bubble markers.
 */
export default function GeoMap({ data, title, height = 350 }: GeoMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || !data.length) return;

    // Dynamic import to avoid SSR issues
    import('leaflet').then((L) => {
      // Fix default marker icons
      delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });

      // Clean up previous instance
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
      }

      const map = L.map(mapRef.current!, {
        scrollWheelZoom: false,
      }).setView([data[0].lat, data[0].lng], 11);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);

      data.forEach((region) => {
        const radius = Math.max(8, Math.sqrt(region.patientCount) * 1.5);
        const color = region.controlRate >= 60 ? '#22c55e' : region.controlRate >= 40 ? '#f59e0b' : '#ef4444';

        L.circleMarker([region.lat, region.lng], {
          radius,
          fillColor: color,
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.7,
        })
          .bindPopup(
            `<div style="font-family: Inter, sans-serif; min-width: 160px;">
              <strong style="font-size: 14px;">${region.name}</strong><br/>
              <span style="color: #64748b; font-size: 12px;">
                Pacientes: <strong>${formatNumber(region.patientCount)}</strong><br/>
                Taxa de Controle: <strong>${formatPercent(region.controlRate)}</strong><br/>
                Alertas: <strong style="color: #ef4444;">${region.alertCount}</strong>
              </span>
            </div>`,
          )
          .addTo(map);
      });

      mapInstanceRef.current = map;
    });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [data]);

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
      {title && <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>}
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        crossOrigin=""
      />
      <div ref={mapRef} style={{ height, width: '100%' }} className="rounded-xl" />
      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> ≥60% controle
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> 40-60%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> &lt;40%
        </span>
      </div>
    </div>
  );
}
