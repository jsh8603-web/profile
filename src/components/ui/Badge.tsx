interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'finance' | 'economy' | 'outline';
  className?: string;
}

export default function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variants = {
    default: 'bg-[#F5F5F7] text-[#1D1D1F]',
    finance: 'bg-[#0071E3]/10 text-[#0071E3]',
    economy: 'bg-emerald-50 text-emerald-700',
    outline: 'border border-[#D2D2D7] text-[#86868B]',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}
