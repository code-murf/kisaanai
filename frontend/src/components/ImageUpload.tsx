/**
 * Image Upload Component
 * File input with image preview and S3 URL display
 */

'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';

interface ImageUploadProps {
  onUpload: (file: File) => void;
  imageUrl?: string;
  disabled?: boolean;
  accept?: string;
}

export function ImageUpload({
  onUpload,
  imageUrl,
  disabled = false,
  accept = 'image/*',
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(imageUrl || null);

  useEffect(() => {
    if (imageUrl) {
      setPreview(imageUrl);
    }
  }, [imageUrl]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Create local preview
      const localPreview = URL.createObjectURL(file);
      setPreview(localPreview);
      onUpload(file);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center w-full">
        <label
          htmlFor="file-upload"
          className={`flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {preview ? (
            <div className="relative w-full h-full">
              <Image
                src={preview}
                alt="Preview"
                fill
                className="object-contain rounded-lg"
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <svg
                className="w-10 h-10 mb-3 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="mb-2 text-sm text-gray-500">
                <span className="font-semibold">फोटो अपलोड करें</span> या खींचें और छोड़ें
              </p>
              <p className="text-xs text-gray-500">PNG, JPG, JPEG (MAX. 10MB)</p>
            </div>
          )}
          <input
            id="file-upload"
            type="file"
            className="hidden"
            accept={accept}
            onChange={handleFileChange}
            disabled={disabled}
          />
        </label>
      </div>

      {preview && (
        <div className="text-center">
          <button
            onClick={() => {
              setPreview(null);
              const input = document.getElementById('file-upload') as HTMLInputElement;
              if (input) input.value = '';
            }}
            className="text-sm text-red-600 hover:text-red-800 underline"
            disabled={disabled}
          >
            फोटो हटाएं (Remove Photo)
          </button>
        </div>
      )}
    </div>
  );
}

export default ImageUpload;
