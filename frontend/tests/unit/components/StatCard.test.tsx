import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatCard from '@/components/common/StatCard';

describe('StatCard', () => {
  it('renders title and value correctly', () => {
    render(
      <StatCard
        title="Total Sites"
        value={42}
        icon="📍"
        trend="+2 this month"
        trendUp={true}
      />
    );

    expect(screen.getByText('Total Sites')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('📍')).toBeInTheDocument();
  });

  it('renders trend with correct color for positive trend', () => {
    render(
      <StatCard
        title="Test"
        value={10}
        icon="📊"
        trend="+5"
        trendUp={true}
      />
    );

    const trend = screen.getByText('+5');
    expect(trend).toHaveClass('text-green-600');
  });

  it('renders trend with correct color for negative trend', () => {
    render(
      <StatCard
        title="Test"
        value={10}
        icon="📊"
        trend="-5"
        trendUp={false}
      />
    );

    const trend = screen.getByText('-5');
    expect(trend).toHaveClass('text-red-600');
  });

  it('applies critical variant styling', () => {
    const { container } = render(
      <StatCard
        title="Critical Issues"
        value={5}
        icon="🚨"
        variant="critical"
      />
    );

    expect(container.firstChild).toHaveClass('border-l-4');
    expect(container.firstChild).toHaveClass('border-l-red-500');
  });
});
