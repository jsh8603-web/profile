'use client';

import { forwardRef, type ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', size = 'md', children, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

    const variants = {
      primary: 'bg-[#0071E3] text-white hover:bg-[#0077ED] active:bg-[#0068D6] shadow-sm',
      secondary: 'bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] active:bg-[#D2D2D7]',
      ghost: 'text-[#0071E3] hover:bg-[#0071E3]/10',
      danger: 'bg-red-500 text-white hover:bg-red-600 active:bg-red-700',
    };

    const sizes = {
      sm: 'text-sm px-3 py-1.5 gap-1.5',
      md: 'text-sm px-5 py-2.5 gap-2',
      lg: 'text-base px-7 py-3 gap-2.5',
    };

    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
export default Button;
