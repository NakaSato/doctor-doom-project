/**
 * Unit Tests for ReportTab Component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReportTab from './ReportTab';

describe('ReportTab', () => {
  const mockProps = {
    data: {
      id: 'INS-TEST-001',
      site: 'Test Solar Farm',
      date: '2026-03-19',
      time: '10:30:00',
    },
    stats: {
      critical: 5,
      major: 10,
      minor: 15,
      totalModules: 96,
      affectedModules: 20,
    },
    healthScore: 75,
  };

  describe('Rendering', () => {
    it('renders report header', () => {
      render(<ReportTab {...mockProps} />);
      
      expect(screen.getByText('THERMOGRAPHIC INSPECTION REPORT')).toBeInTheDocument();
      expect(screen.getByText('Test Solar Farm')).toBeInTheDocument();
      expect(screen.getByText('INS-TEST-001')).toBeInTheDocument();
    });

    it('displays 4 stat boxes', () => {
      render(<ReportTab {...mockProps} />);
      
      expect(screen.getByText('Critical')).toBeInTheDocument();
      expect(screen.getByText('Major')).toBeInTheDocument();
      expect(screen.getByText('Minor')).toBeInTheDocument();
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });

    it('shows correct stat values', () => {
      render(<ReportTab {...mockProps} />);
      
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('76')).toBeInTheDocument(); // 96 - 20
    });
  });

  describe('Health Score', () => {
    it('displays health score', () => {
      render(<ReportTab {...mockProps} />);
      
      expect(screen.getByText('Array Health Score')).toBeInTheDocument();
      expect(screen.getByText('75')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });

    it('colors health score based on value', () => {
      const { rerender } = render(
        <ReportTab {...mockProps} healthScore={85} />
      );
      
      const scoreElement = screen.getByText('85');
      expect(scoreElement).toHaveStyle('color: #2CB67D'); // Green for > 80
      
      rerender(<ReportTab {...mockProps} healthScore={65} />);
      const scoreElement2 = screen.getByText('65');
      expect(scoreElement2).toHaveStyle('color: #FF9500'); // Orange for 60-80
      
      rerender(<ReportTab {...mockProps} healthScore={50} />);
      const scoreElement3 = screen.getByText('50');
      expect(scoreElement3).toHaveStyle('color: #FF3B30'); // Red for < 60
    });
  });

  describe('Stat Box Colors', () => {
    it('displays critical in red', () => {
      render(<ReportTab {...mockProps} />);
      
      const criticalValue = screen.getByText('5');
      const parent = criticalValue.parentElement;
      expect(parent).toHaveStyle('border: 1px solid #FF3B3030');
    });

    it('displays major in orange', () => {
      render(<ReportTab {...mockProps} />);
      
      const majorValue = screen.getByText('10');
      const parent = majorValue.parentElement;
      expect(parent).toHaveStyle('border: 1px solid #FF950030');
    });

    it('displays minor in yellow', () => {
      render(<ReportTab {...mockProps} />);
      
      const minorValue = screen.getByText('15');
      const parent = minorValue.parentElement;
      expect(parent).toHaveStyle('border: 1px solid #FFCC0030');
    });

    it('displays healthy in green', () => {
      render(<ReportTab {...mockProps} />);
      
      const healthyValue = screen.getByText('76');
      const parent = healthyValue.parentElement;
      expect(parent).toHaveStyle('border: 1px solid #2CB67D30');
    });
  });

  describe('Stub Message', () => {
    it('shows coming soon message', () => {
      render(<ReportTab {...mockProps} />);
      
      expect(screen.getByText('Report generation coming soon')).toBeInTheDocument();
      expect(screen.getByText('Full IEC 62446-3 compliant reports will be available in the next update')).toBeInTheDocument();
    });

    it('displays checkmark icon', () => {
      render(<ReportTab {...mockProps} />);
      
      expect(screen.getByText('✅')).toBeInTheDocument();
    });
  });

  describe('Null Data', () => {
    it('returns null when no data', () => {
      const { container } = render(
        <ReportTab data={null} stats={{}} healthScore={0} as any />
      );
      
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Layout', () => {
    it('has centered text alignment in header', () => {
      render(<ReportTab {...mockProps} />);
      
      const header = screen.getByText('THERMOGRAPHIC INSPECTION REPORT').parentElement;
      expect(header).toHaveStyle('text-align: center');
    });

    it('has grid layout for stat boxes', () => {
      render(<ReportTab {...mockProps} />);
      
      const grid = screen.getByText('Critical').parentElement?.parentElement;
      expect(grid).toHaveStyle('display: grid');
      expect(grid).toHaveStyle('grid-template-columns: repeat(4, 1fr)');
    });
  });
});
