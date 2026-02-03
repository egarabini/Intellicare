import { motion } from 'framer-motion';

interface AgentFiltersProps {
  categories: string[];
  activeCategory: string;
  onCategoryChange: (category: string) => void;
}

export default function AgentFilters({
  categories,
  activeCategory,
  onCategoryChange,
}: AgentFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3 mb-8">
      {categories.map((category) => (
        <motion.button
          key={category}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onCategoryChange(category)}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            activeCategory === category
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-white text-neutral-700 border-2 border-neutral-200 hover:border-primary-300'
          }`}
        >
          {category}
        </motion.button>
      ))}
    </div>
  );
}
