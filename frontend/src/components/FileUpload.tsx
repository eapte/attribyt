import { useRef } from "react";

interface Props {
  onFileSelected: (file: File) => void;
  fileName: string | null;
}

export default function FileUpload({ onFileSelected, fileName }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="file-upload">
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFileSelected(file);
        }}
        hidden
      />
      <button className="btn-secondary" onClick={() => inputRef.current?.click()}>
        {fileName ? "Replace file" : "Choose CSV"}
      </button>
      {fileName && <span className="file-name">{fileName}</span>}
    </div>
  );
} 