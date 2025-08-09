'use client';

import { getFacultyAbbreviation, getYearDisplayText } from '@/lib/actions/updateProfile';

// Author information type (matches backend PublicProfile)
export interface AuthorAffiliation {
  faculty: string | null;
  year: number | null;
}

export interface AuthorChipProps {
  authorAffiliation: AuthorAffiliation | null;
  size?: 'sm' | 'md';
  className?: string;
}

/**
 * Get faculty color class for styling
 */
function getFacultyColorClass(faculty: string | null): string {
  if (!faculty) {
    return 'bg-gray-100 text-gray-600 border-gray-200';
  }
  
  // Faculty-specific color palette
  const facultyColors: Record<string, string> = {
    '文学部': 'bg-purple-100 text-purple-700 border-purple-200',
    '教育学部': 'bg-green-100 text-green-700 border-green-200', 
    '法学部': 'bg-blue-100 text-blue-700 border-blue-200',
    '経済学部': 'bg-yellow-100 text-yellow-700 border-yellow-200',
    '理学部': 'bg-indigo-100 text-indigo-700 border-indigo-200',
    '医学部': 'bg-red-100 text-red-700 border-red-200',
    '歯学部': 'bg-pink-100 text-pink-700 border-pink-200',
    '薬学部': 'bg-teal-100 text-teal-700 border-teal-200',
    '工学部': 'bg-orange-100 text-orange-700 border-orange-200',
    '芸術工学部': 'bg-rose-100 text-rose-700 border-rose-200',
    '農学部': 'bg-lime-100 text-lime-700 border-lime-200',
    '共創学部': 'bg-cyan-100 text-cyan-700 border-cyan-200',
  };
  
  return facultyColors[faculty] || 'bg-slate-100 text-slate-700 border-slate-200';
}

/**
 * Get size-specific classes
 */
function getSizeClasses(size: 'sm' | 'md'): string {
  switch (size) {
    case 'sm':
      return 'text-xs px-1.5 py-0.5 gap-1';
    case 'md':
      return 'text-sm px-2 py-1 gap-1.5';
    default:
      return 'text-sm px-2 py-1 gap-1.5';
  }
}

/**
 * AuthorChip Component
 * 
 * Displays author's faculty and year as compact badges
 * with faculty-specific color coding and responsive design.
 */
export default function AuthorChip({ 
  authorAffiliation, 
  size = 'sm',
  className = '' 
}: AuthorChipProps) {
  // Handle null or empty affiliation
  if (!authorAffiliation || (!authorAffiliation.faculty && !authorAffiliation.year)) {
    return null;
  }
  
  const { faculty, year } = authorAffiliation;
  
  // Get display values
  const facultyAbbr = getFacultyAbbreviation(faculty);
  const yearDisplay = getYearDisplayText(year);
  
  // Get styling classes
  const colorClass = getFacultyColorClass(faculty);
  const sizeClass = getSizeClasses(size);
  
  // Don't render if both are default values
  if (facultyAbbr === '未設定' && yearDisplay === '未設定') {
    return null;
  }
  
  return (
    <div className={`inline-flex items-center justify-center rounded-full border font-medium ${colorClass} ${sizeClass} ${className}`}>
      {facultyAbbr !== '未設定' && (
        <span className="font-semibold" aria-label={`学部: ${faculty || '未設定'}`}>
          {facultyAbbr}
        </span>
      )}
      {facultyAbbr !== '未設定' && yearDisplay !== '未設定' && (
        <span className="text-current opacity-60" aria-hidden="true">•</span>
      )}
      {yearDisplay !== '未設定' && (
        <span aria-label={`学年: ${yearDisplay}`}>
          {yearDisplay}
        </span>
      )}
    </div>
  );
}