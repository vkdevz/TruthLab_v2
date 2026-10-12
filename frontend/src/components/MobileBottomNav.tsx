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
  const navItems: { id: MobileSectionTab; label: string; symbol: string; targetId: string }[] = [
    { id: 'VERIFY', label: 'Verify', symbol: '◉', targetId: 'workbench' },
    { id: 'PIPELINE', label: 'Pipeline', symbol: '◫', targetId: 'architecture' },
    { id: 'BENCHMARKS', label: 'Evaluation', symbol: '▤', targetId: 'benchmarks' },
    { id: 'METHODS', label: 'Methods', symbol: '⌬', targetId: 'methodology' },
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
              const el = document.getElementById(item.targetId);
              if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
              } else {
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }
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
