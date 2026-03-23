"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Upload, FileText, X, Loader2 } from "lucide-react";

interface PdfUploadProps {
  onUploadComplete: (result: any) => void;
  onClose: () => void;
  lastUploadResult?: any;
}

export function PdfUpload({ onUploadComplete, onClose, lastUploadResult }: PdfUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number>(0);
  const [uploadResult, setUploadResult] = useState<any>(lastUploadResult || null);
  const [showPreview, setShowPreview] = useState(!!lastUploadResult);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf") {
        setError("Please upload a PDF file.");
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        setError("File too large. Max 20 MB.");
        return;
      }

      setError(null);
      setFileName(file.name);
      setFileSize(file.size);
      setIsUploading(true);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          throw new Error(`Upload failed: ${res.statusText}`);
        }

        const result = await res.json();
        setUploadResult(result);
        setShowPreview(true);
        onUploadComplete(result);
      } catch (err: any) {
        setError(err.message || "Upload failed.");
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Upload brokerage statement"
    >
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Upload Statement</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X size={20} />
          </button>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
            ${isDragging ? "border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30" : "border-slate-200 dark:border-slate-700 hover:border-emerald-300 hover:bg-slate-50 dark:hover:bg-slate-800"}
          `}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            onChange={handleInputChange}
            className="hidden"
          />

          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 size={32} className="text-emerald-600 animate-spin" />
              <p className="text-sm text-slate-600">Processing {fileName}...</p>
            </div>
          ) : fileName && !error ? (
            <div className="flex flex-col items-center gap-3">
              <FileText size={32} className="text-emerald-600" />
              <p className="text-sm text-slate-600">{fileName}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload size={32} className="text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-700">
                  Drop your brokerage statement here
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  PDF up to 20 MB — RBC, TD, Wealthsimple, Questrade & more
                </p>
              </div>
            </div>
          )}
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-500">{error}</p>
        )}

        {/* Upload preview card */}
        {showPreview && uploadResult && (
          <div className="mt-4 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/20 p-3">
            <div className="flex items-start gap-3">
              <FileText size={20} className="text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                  {fileName || "Uploaded statement"}
                </p>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {fileSize > 0 && <span>{(fileSize / 1024).toFixed(0)} KB</span>}
                  <span>{uploadResult.institution || "Unknown"}</span>
                  {uploadResult.accounts && (
                    <span>
                      {uploadResult.accounts.reduce(
                        (sum: number, a: any) => sum + (a.holdings?.length || 0),
                        0
                      )}{" "}
                      holdings
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                setShowPreview(false);
                setUploadResult(null);
                setFileName(null);
                setFileSize(0);
              }}
              className="mt-2 text-xs text-emerald-600 dark:text-emerald-400 hover:underline font-medium"
            >
              Upload another
            </button>
          </div>
        )}

        <p className="mt-4 text-xs text-slate-400 text-center">
          Your statement is processed locally and never stored permanently.
        </p>
      </div>
    </div>
  );
}
