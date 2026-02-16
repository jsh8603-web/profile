'use client';

import { forwardRef, type InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', label, error, id, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-[#1D1D1F] mb-1.5">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={`w-full px-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-[#1D1D1F] text-sm placeholder:text-[#86868B] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all duration-200 ${error ? 'border-red-400 focus:ring-red-400/30' : ''} ${className}`}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
export default Input;
