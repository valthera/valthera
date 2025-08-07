import { useFeatureFlag } from '../contexts/FeatureFlagsContext';
import { AIAssistant } from './AIAssistant';

interface AIAssistantWrapperProps {
  isOpen: boolean;
  onClose: () => void;
  width: number;
  isMobile: boolean;
  onResize: (e: React.MouseEvent) => void;
}

export function AIAssistantWrapper({ isOpen, onClose, width, isMobile, onResize }: AIAssistantWrapperProps) {
  const isAIAssistantEnabled = useFeatureFlag('aiResearchAssistant');

  if (!isAIAssistantEnabled) {
    return null; // Don't render anything if the feature is disabled
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className={`fixed top-0 right-0 h-full bg-white border-l border-gray-200 z-40 transition-all duration-300 ${
        isMobile ? 'w-full' : ''
      }`}
      style={{
        width: isMobile ? '100%' : `${width}px`,
        transform: isOpen ? 'translateX(0)' : 'translateX(100%)'
      }}
    >
      {/* Resize handle for desktop */}
      {!isMobile && (
        <div
          className="absolute left-0 top-0 w-1 h-full cursor-col-resize hover:bg-gray-300 transition-colors"
          onMouseDown={onResize}
        />
      )}
      
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 text-gray-500 hover:text-gray-700 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <AIAssistant />
    </div>
  );
} 