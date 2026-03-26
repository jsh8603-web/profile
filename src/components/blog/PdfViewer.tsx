'use client';

import { useState, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, Download, Loader2 } from 'lucide-react';

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PdfViewerProps {
  url: string;
  fileName?: string;
}

export default function PdfViewer({ url, fileName }: PdfViewerProps) {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    if (containerRef.current) {
      setContainerWidth(containerRef.current.clientWidth);
    }
  }, []);

  const goToPrev = () => setPageNumber((p) => Math.max(1, p - 1));
  const goToNext = () => setPageNumber((p) => Math.min(numPages, p + 1));

  return (
    <div ref={containerRef} className="flex flex-col items-center">
      {/* Controls */}
      <div className="sticky top-0 z-10 flex items-center gap-4 py-3 px-4 bg-white/90 backdrop-blur-sm border-b border-[#E8E8ED] w-full justify-center">
        <button
          onClick={goToPrev}
          disabled={pageNumber <= 1}
          className="p-2 rounded-full hover:bg-[#F5F5F7] disabled:opacity-30 transition-colors"
        >
          <ChevronLeft size={20} />
        </button>

        <span className="text-sm font-medium text-[#1D1D1F] min-w-[80px] text-center">
          {pageNumber} / {numPages || '—'}
        </span>

        <button
          onClick={goToNext}
          disabled={pageNumber >= numPages}
          className="p-2 rounded-full hover:bg-[#F5F5F7] disabled:opacity-30 transition-colors"
        >
          <ChevronRight size={20} />
        </button>

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-4 p-2 rounded-full hover:bg-[#F5F5F7] transition-colors text-[#86868B] hover:text-[#0071E3]"
          title={fileName || 'Download PDF'}
        >
          <Download size={18} />
        </a>
      </div>

      {/* PDF Document */}
      <div className="mt-4 w-full flex justify-center">
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="flex items-center justify-center py-32">
              <Loader2 className="animate-spin text-[#86868B]" size={32} />
            </div>
          }
          error={
            <div className="text-center py-20 text-[#86868B]">
              <p>Failed to load PDF.</p>
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            width={containerWidth ? Math.min(containerWidth - 32, 1350) : undefined}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            canvasBackground="white"
            onRenderSuccess={() => {
              // Force-remove any annotation/text layers that react-pdf may inject
              const layers = containerRef.current?.querySelectorAll(
                '.annotationLayer, .textLayer, .react-pdf__Page__annotationLayer, .react-pdf__Page__textLayer'
              );
              layers?.forEach((el) => el.remove());
            }}
          />
        </Document>
      </div>
    </div>
  );
}
