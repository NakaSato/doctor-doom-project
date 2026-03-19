/**
 * Unit Tests for TempScale Component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TempScale from './TempScale';

describe('TempScale', () => {
  describe('Rendering', () => {
    it('renders with default unit (°C)', () => {
      render(<TempScale min={35} max={70} />);
      
      expect(screen.getByText('35°C')).toBeInTheDocument();
      expect(screen.getByText('70°C')).toBeInTheDocument();
    });

    it('renders with custom unit', () => {
      render(<TempScale min={95} max={158} unit="°F" />);
      
      expect(screen.getByText('95°F')).toBeInTheDocument();
      expect(screen.getByText('158°F')).toBeInTheDocument();
    });

    it('displays gradient background', () => {
      const { container } = render(<TempScale min={35} max={70} />);
      
      const gradientBar = container.firstChild?.childNodes[1] as HTMLElement;
      expect(gradientBar).toHaveStyle(
        'background: linear-gradient(to right, #000033, #000066, #000099, #0033cc, #0066ff, #00ccff, #00ff00, #ffff00, #ff9900, #ff3300, #ff0000)'
      );
    });

    it('displays marker lines', () => {
      const { container } = render(<TempScale min={35} max={70} />);
      
      // Should have 3 marker lines at 25%, 50%, 75%
      const markers = container.querySelectorAll('[style*="position: absolute"]');
      expect(markers.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Styling', () => {
    it('has rounded corners', () => {
      const { container } = render(<TempScale min={35} max={70} />);
      
      const container_element = container.firstChild as HTMLElement;
      expect(container_element).toHaveStyle('border-radius: 8px');
    });

    it('has proper padding', () => {
      const { container } = render(<TempScale min={35} max={70} />);
      
      const container_element = container.firstChild as HTMLElement;
      expect(container_element).toHaveStyle('padding: 12px');
    });

    it('has gradient bar with shadow', () => {
      const { container } = render(<TempScale min={35} max={70} />);
      
      const gradientBar = container.firstChild?.childNodes[1] as HTMLElement;
      expect(gradientBar).toHaveStyle('box-shadow: 0 2px 8px rgba(0,0,0,0.3)');
    });
  });

  describe('Layout', () => {
    it('displays min value on left', () => {
      render(<TempScale min={35} max={70} />);
      
      const minLabel = screen.getByText('35°C');
      const container_element = minLabel.parentElement;
      expect(container_element).toBeInTheDocument();
    });

    it('displays max value on right', () => {
      render(<TempScale min={35} max={70} />);
      
      const maxLabel = screen.getByText('70°C');
      expect(maxLabel).toBeInTheDocument();
    });

    it('has flex layout', () => {
      const { container } = render(<TempScale min={35} max={70} />);
      
      const container_element = container.firstChild as HTMLElement;
      expect(container_element).toHaveStyle('display: flex');
      expect(container_element).toHaveStyle('align-items: center');
    });
  });

  describe('Accessibility', () => {
    it('has proper font styling', () => {
      render(<TempScale min={35} max={70} />);
      
      const minLabel = screen.getByText('35°C');
      expect(minLabel).toHaveStyle('font-family: monospace');
      expect(minLabel).toHaveStyle('font-weight: 600');
    });

    it('has readable color contrast', () => {
      render(<TempScale min={35} max={70} />);
      
      const minLabel = screen.getByText('35°C');
      expect(minLabel).toHaveStyle('color: #aaa');
    });
  });

  describe('Edge Cases', () => {
    it('handles negative temperatures', () => {
      render(<TempScale min={-10} max={10} />);
      
      expect(screen.getByText('-10°C')).toBeInTheDocument();
      expect(screen.getByText('10°C')).toBeInTheDocument();
    });

    it('handles same min and max', () => {
      render(<TempScale min={50} max={50} />);
      
      expect(screen.getByText('50°C')).toBeInTheDocument();
    });

    it('handles large temperature range', () => {
      render(<TempScale min={0} max={1000} />);
      
      expect(screen.getByText('0°C')).toBeInTheDocument();
      expect(screen.getByText('1000°C')).toBeInTheDocument();
    });
  });
});
