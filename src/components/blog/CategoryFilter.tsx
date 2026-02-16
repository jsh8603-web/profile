'use client';

interface CategoryFilterProps {
  selected: string;
  onChange: (category: string) => void;
}

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'finance', label: 'Finance' },
  { value: 'economy', label: 'Economy' },
];

export default function CategoryFilter({ selected, onChange }: CategoryFilterProps) {
  return (
    <div className="flex items-center gap-2">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          onClick={() => onChange(cat.value)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
            selected === cat.value
              ? 'bg-[#1D1D1F] text-white'
              : 'bg-[#F5F5F7] text-[#424245] hover:bg-[#E8E8ED]'
          }`}
        >
          {cat.label}
        </button>
      ))}
    </div>
  );
}
