import { useRef } from "react";

interface Props {
  onFileSelected: (file: File) => void;
  fileName: string | null;
  hero?: boolean;
}

export default function FileUpload({ onFileSelected, fileName, hero }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  const input = (
    <input
      ref={inputRef}
      type="file"
      accept=".csv,.xlsx,.xls"
      onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) onFileSelected(file);
      }}
      hidden
    />
  );

  if (hero) {
    return (
      <div className="hero-upload-row">
        <span className="format-badge">CSV</span>
        {input}
        <button className="btn-primary" onClick={() => inputRef.current?.click()}>
          Choose file
        </button>
        <span className="format-badge">XLSX</span>
      </div>
    );
  }

  return (
    <div className="file-upload">
      {input}
      <button className="btn-secondary" onClick={() => inputRef.current?.click()}>
        {fileName ? "Replace file" : "Choose file"}
      </button>
      {fileName && <span className="file-name">{fileName}</span>}
    </div>
  );
} 