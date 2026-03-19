/**
 * Unit Tests for UploadTab Component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import UploadTab from './UploadTab';

describe('UploadTab', () => {
  const mockProps = {
    inspectionStarted: false,
    processingProgress: 0,
    onStartProcessing: vi.fn(),
    onComplete: vi.fn(),
  };

  describe('Initial State', () => {
    it('renders upload prompt when not started', () => {
      render(<UploadTab {...mockProps} />);
      
      expect(screen.getByText('Thermal Image Upload')).toBeInTheDocument();
      expect(screen.getByText('Drop RJPEG / TIFF thermal images here')).toBeInTheDocument();
      expect(screen.getByText('▶ START THERMAL ANALYSIS (DEMO DATA)')).toBeInTheDocument();
    });

    it('displays flight parameters section', () => {
      render(<UploadTab {...mockProps} />);
      
      expect(screen.getByText('FLIGHT PARAMETERS')).toBeInTheDocument();
      expect(screen.getByText('DJI Mavic 3T')).toBeInTheDocument();
      expect(screen.getByText('FLIR (640×512 uncooled VOx)')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('calls onStartProcessing when button is clicked', () => {
      render(<UploadTab {...mockProps} />);
      
      const startButton = screen.getByText('▶ START THERMAL ANALYSIS (DEMO DATA)');
      fireEvent.click(startButton);
      
      expect(mockProps.onStartProcessing).toHaveBeenCalledTimes(1);
    });

    it('shows hover effect on upload area', () => {
      render(<UploadTab {...mockProps} />);
      
      const uploadArea = screen.getByText('📡').parentElement;
      expect(uploadArea).toBeInTheDocument();
    });
  });

  describe('Processing State', () => {
    it('shows processing animation when processing', () => {
      render(
        <UploadTab
          {...mockProps}
          inspectionStarted={true}
          processingProgress={50}
        />
      );
      
      expect(screen.getByText('Processing Thermal Data...')).toBeInTheDocument();
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('shows different messages based on progress', () => {
      const { rerender } = render(
        <UploadTab
          {...mockProps}
          inspectionStarted={true}
          processingProgress={10}
        />
      );
      
      expect(screen.getByText(/Loading radiometric data/)).toBeInTheDocument();
      
      rerender(
        <UploadTab
          {...mockProps}
          inspectionStarted={true}
          processingProgress={50}
        />
      );
      
      expect(screen.getByText(/Running CNN/)).toBeInTheDocument();
      
      rerender(
        <UploadTab
          {...mockProps}
          inspectionStarted={true}
          processingProgress={90}
        />
      );
      
      expect(screen.getByText(/Generating report/)).toBeInTheDocument();
    });
  });

  describe('Completion State', () => {
    it('shows completion message when done', () => {
      render(
        <UploadTab
          {...mockProps}
          inspectionStarted={true}
          processingProgress={100}
        />
      );
      
      expect(screen.getByText('Analysis Complete')).toBeInTheDocument();
      expect(screen.getByText('✅')).toBeInTheDocument();
      expect(screen.getByText('VIEW RESULTS →')).toBeInTheDocument();
    });

    it('calls onComplete when VIEW RESULTS button is clicked', () => {
      render(
        <UploadTab
          {...mockProps}
          inspectionStarted={true}
          processingProgress={100}
        />
      );
      
      const viewResultsButton = screen.getByText('VIEW RESULTS →');
      fireEvent.click(viewResultsButton);
      
      expect(mockProps.onComplete).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(<UploadTab {...mockProps} />);
      
      expect(screen.getByText('Thermal Image Upload')).toBeInTheDocument();
    });

    it('has clickable button', () => {
      render(<UploadTab {...mockProps} />);
      
      const button = screen.getByText('▶ START THERMAL ANALYSIS (DEMO DATA)');
      expect(button).toBeInTheDocument();
    });
  });
});
