import React from 'react';

export type MobileSectionTab = 'VERIFY' | 'PIPELINE' | 'BENCHMARKS' | 'METHODS';

interface MobileBottomNavProps {
  activeSection: MobileSectionTab;
  onSelectSection: (section: MobileSectionTab) => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  activeSection,
  onSelectSection,
}) => {
  const navItems: { id: MobileSectionTab; label: string; symbol: string }[] = [
    { id: 'VERIFY', label: 'Verify', symbol: '◉' },
    { id: 'PIPELINE', label: 'Pipeline', symbol: '◫' },
    { id: 'BENCHMARKS', label: 'Evaluation', symbol: '▤' },
    { id: 'METHODS', label: 'Methods', symbol: '⌬' },
  ];

  return (
    <nav className="m-bottom-nav m-mobile-only" aria-label="Mobile section navigation">
      {navItems.map((item) => {
        const isActive = activeSection === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => {
              onSelectSection(item.id);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            className={`m-bottom-nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="m-bottom-nav-icon">{item.symbol}</span>
            <span className="m-bottom-nav-label">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
};
