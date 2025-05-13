import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

interface FileUploadProps {
  onSubmit: (files: File[], parser: string) => void;
  isUploading: boolean;
}

export function FileUpload({ onSubmit, isUploading }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [parser, setParser] = useState<string>('pypdf');
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    // Filter for PDF files
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== acceptedFiles.length) {
      setError('Only PDF files are allowed.');
    }
    
    if (pdfFiles.length > 0) {
      setFiles(pdfFiles);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    }
  });

  const handleSubmit = () => {
    if (files.length === 0) {
      setError('Please upload at least one PDF file');
      return;
    }

    if (!parser) {
      setError('Please select a parser');
      return;
    }

    onSubmit(files, parser);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 transition-colors ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-border'
        } cursor-pointer`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <UploadCloud className="h-12 w-12 text-muted-foreground" />
          <div className="space-y-2">
            <h3 className="font-medium text-lg">Drag and drop your PDF files here</h3>
            <p className="text-sm text-muted-foreground">
              Or click to browse (PDF files only)
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center text-sm">
          <AlertCircle className="h-4 w-4 mr-2 text-destructive" />
          <span className="text-destructive">{error}</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium mb-3">Selected Files</h4>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li key={index} className="flex items-center p-3 bg-secondary rounded-lg">
                <File className="h-5 w-5 mr-2 text-primary" />
                <span className="text-sm">{file.name}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <h4 className="text-sm font-medium mb-3">Select Parser</h4>
        <RadioGroup value={parser} onValueChange={setParser} className="flex flex-col space-y-2">
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="pypdf" id="pypdf" />
            <Label htmlFor="pypdf">PyPDF (Basic text extraction)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="gemini" id="gemini" />
            <Label htmlFor="gemini">Google Gemini (Rich markdown with formatting)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="mistral" id="mistral" />
            <Label htmlFor="mistral">Mistral (Experimental)</Label>
          </div>
        </RadioGroup>
      </div>

      <Button 
        onClick={handleSubmit} 
        className="mt-6 w-full"
        disabled={isUploading || files.length === 0}
      >
        {isUploading ? "Uploading..." : "Upload and Process"}
      </Button>
    </div>
  );
} 