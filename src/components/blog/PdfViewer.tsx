'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';

interface PdfViewerProps {
  url: string;
  fileName?: string;
}

export default function PdfViewer({ url, fileName }: PdfViewerProps) {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="flex flex-col items-center w-full">
      {/* Download link */}
      <div className="flex items-center justify-end py-3 px-4 bg-white/90 backdrop-blur-sm border-b border-[#E8E8ED] w-full">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-full hover:bg-[#F5F5F7] transition-colors text-[#86868B] hover:text-[#0071E3]"
          title={fileName || 'Download PDF'}
        >
          <Download size={18} />
        </a>
      </div>

      {/* PDF iframe - uses browser's native PDF renderer */}
      <div className="mt-2 w-full" style={{ height: '80vh', minHeight: '600px' }}>
        {!loaded && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#86868B]" />
          </div>
        )}
        <iframe
          src={url}
          className="w-full h-full border-0 rounded-lg"
          title={fileName || 'PDF Document'}
          onLoad={() => setLoaded(true)}
          style={{ display: loaded ? 'block' : 'none' }}
        />
      </div>
    </div>
  );
}
