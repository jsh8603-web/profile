interface SkeletonProps {
  className?: string;
}

export default function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div className={`animate-pulse bg-[#F5F5F7] rounded-xl ${className}`} />
  );
}
