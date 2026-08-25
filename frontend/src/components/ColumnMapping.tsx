import type { ColumnMapping as ColumnMappingType } from "../types";

interface Props {
  headers: string[];
  mapping: ColumnMappingType;
  onChange: (mapping: ColumnMappingType) => void;
}

const FIELDS: { key: keyof ColumnMappingType; label: string }[] = [
  { key: "user_col", label: "User ID" },
  { key: "timestamp_col", label: "Event time" },
  { key: "channel_col", label: "Channel" },
  { key: "event_col", label: "Event type" },
  { key: "revenue_col", label: "Revenue" },
];

/**
 * Guesses which CSV header matches each required field, based on
 * common naming patterns. Falls back to the first header if nothing
 * matches, so a dropdown is never left empty.
 */
export function guessMapping(headers: string[]): ColumnMappingType {
  const patterns: Record<keyof ColumnMappingType, RegExp> = {
    user_col: /user|client|customer/i,
    timestamp_col: /time|date/i,
    channel_col: /channel|source|traffic|medium/i,
    event_col: /^action$|event_type|event_name|^type$/i,
    revenue_col: /revenue|amount|price|value|total/i,
  };

  const result = {} as ColumnMappingType;
  for (const field of FIELDS) {
    const match = headers.find((h) => patterns[field.key].test(h));
    result[field.key] = match ?? headers[0] ?? "";
  }
  return result;
}

export default function ColumnMappingForm({ headers, mapping, onChange }: Props) {
  return (
    <div className="column-mapping">
      <h3>Column mapping</h3>
      <p className="hint">Auto-detected — review and adjust if needed.</p>
      <div className="mapping-grid">
        {FIELDS.map(({ key, label }) => (
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
      </div>
    </div>
  );
} 