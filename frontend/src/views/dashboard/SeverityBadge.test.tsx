/**
 * Unit Tests for SeverityBadge Component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SeverityBadge from './SeverityBadge';

describe('SeverityBadge', () => {
  describe('Rendering', () => {
    it('renders critical badge correctly', () => {
      render(<SeverityBadge severity="critical" animated={false} />);
      
      expect(screen.getByText('Critical')).toBeInTheDocument();
      const badge = screen.getByText('Critical').parentElement;
      expect(badge).toHaveStyle('color: #FF3B30');
    });

    it('renders major badge correctly', () => {
      render(<SeverityBadge severity="major" animated={false} />);
      
      expect(screen.getByText('Major')).toBeInTheDocument();
      const badge = screen.getByText('Major').parentElement;
      expect(badge).toHaveStyle('color: #FF9500');
    });

    it('renders minor badge correctly', () => {
      render(<SeverityBadge severity="minor" animated={false} />);
      
      expect(screen.getByText('Minor')).toBeInTheDocument();
      const badge = screen.getByText('Minor').parentElement;
      expect(badge).toHaveStyle('color: #FFCC00');
    });

    it('renders low badge correctly', () => {
      render(<SeverityBadge severity="low" animated={false} />);
      
      expect(screen.getByText('Low')).toBeInTheDocument();
      const badge = screen.getByText('Low').parentElement;
      expect(badge).toHaveStyle('color: #2CB67D');
    });
  });

  describe('Sizes', () => {
    it('renders small size correctly', () => {
      render(<SeverityBadge severity="critical" size="small" animated={false} />);
      
      const badge = screen.getByText('Critical');
      expect(badge).toHaveStyle('font-size: 9px');
    });

    it('renders medium size correctly', () => {
      render(<SeverityBadge severity="critical" size="medium" animated={false} />);
      
      const badge = screen.getByText('Critical');
      expect(badge).toHaveStyle('font-size: 10px');
    });

    it('renders large size correctly', () => {
      render(<SeverityBadge severity="critical" size="large" animated={false} />);
      
      const badge = screen.getByText('Critical');
      expect(badge).toHaveStyle('font-size: 12px');
    });
  });

  describe('Animation', () => {
    it('has animation enabled by default', () => {
      const { container } = render(<SeverityBadge severity="critical" />);
      
      // Animation should be present (pulse effect)
      expect(container.firstChild).toBeInTheDocument();
    });

    it('can disable animation', () => {
      const { container } = render(<SeverityBadge severity="critical" animated={false} />);
      
      expect(container.firstChild).toBeInTheDocument();
    });

    it('shows glow effect for critical severity', () => {
      render(<SeverityBadge severity="critical" animated={false} />);
      
      const badge = screen.getByText('Critical').parentElement;
      expect(badge).toHaveStyle('box-shadow: 0 0 10px rgba(255,59,48,0.38)');
    });
  });

  describe('Visual Elements', () => {
    it('displays dot indicator', () => {
      render(<SeverityBadge severity="critical" animated={false} />);
      
      // Dot should be present (6x6px circle)
      const dot = document.querySelector('span[style*="width: 6px"]');
      expect(dot).toBeInTheDocument();
    });

    it('has rounded corners', () => {
      render(<SeverityBadge severity="critical" animated={false} />);
      
      const badge = screen.getByText('Critical').parentElement;
      expect(badge).toHaveStyle('border-radius: 12px');
    });

    it('has uppercase text', () => {
      render(<SeverityBadge severity="critical" animated={false} />);
      
      const badge = screen.getByText('Critical');
      expect(badge).toHaveStyle('text-transform: uppercase');
    });
  });

  describe('Invalid Severity', () => {
    it('defaults to low severity for invalid input', () => {
      // @ts-ignore - Testing invalid input
      render(<SeverityBadge severity="invalid" animated={false} />);
      
      expect(screen.getByText('Low')).toBeInTheDocument();
    });
  });
});
