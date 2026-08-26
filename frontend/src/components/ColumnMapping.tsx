import type { ColumnMapping as ColumnMappingType } from "../types";

interface Props {
  headers: string[];
  mapping: ColumnMappingType;
  onChange: (mapping: ColumnMappingType) => void;
}

const REQUIRED_FIELDS: { key: keyof ColumnMappingType; label: string }[] = [
  { key: "user_col", label: "User ID" },
  { key: "timestamp_col", label: "Event time" },
  { key: "channel_col", label: "Channel" },
  { key: "revenue_col", label: "Revenue" },
];

export function guessMapping(headers: string[]): ColumnMappingType {
  const patterns: Record<keyof Omit<ColumnMappingType, "segment_col">, RegExp> = {
    user_col: /user|client|customer/i,
    timestamp_col: /time|date/i,
    channel_col: /channel|source|traffic|medium/i,
    revenue_col: /revenue|amount|price|value|total/i,
  };

  const result = {} as ColumnMappingType;
  for (const field of REQUIRED_FIELDS) {
    const key = field.key as keyof Omit<ColumnMappingType, "segment_col">;
    const match = headers.find((h) => patterns[key].test(h));
    result[field.key] = match ?? headers[0] ?? "";
  }
  result.segment_col = "";
  return result;
}

export default function ColumnMappingForm({ headers, mapping, onChange }: Props) {
  return (
    <div className="column-mapping">
      <h3>Column mapping</h3>
      <p className="hint">Auto-detected — review and adjust if needed.</p>
      <div className="mapping-grid">
        {REQUIRED_FIELDS.map(({ key, label }) => (
          <label key={key} className="mapping-field">
            <span>{label}</span>
            <select
              value={mapping[key]}
              onChange={(e) => onChange({ ...mapping, [key]: e.target.value })}
            >
              {headers.map((h) => (
                <option key={h} value={h}>
                  {h}
                </option>
              ))}
            </select>
          </label>
        ))}

        <label className="mapping-field">
          <span>Segment by (optional)</span>
          <select
            value={mapping.segment_col}
            onChange={(e) => onChange({ ...mapping, segment_col: e.target.value })}
          >
            <option value="">None</option>
            {headers.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
} 